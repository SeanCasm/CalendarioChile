from datetime import date, timedelta
import secrets
from urllib.parse import urlencode
from urllib.parse import quote, urljoin, urlparse

from django.core.cache import cache
from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse
import requests
from dotenv import load_dotenv
import os

load_dotenv()

MONTH_NAMES = [
    "Enero",
    "Febrero",
    "Marzo",
    "Abril",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Septiembre",
    "Octubre",
    "Noviembre",
    "Diciembre",
]

GOOGLE_AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_CALENDAR_EVENTS_URL = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
GOOGLE_CALENDAR_SCOPE = "https://www.googleapis.com/auth/calendar.events"

def make_event(
    event_date,
    title,
    event_type,
    scope=None,
    category=None,
    is_holiday=False,
    irrenunciable=False,
    **extra,
):
    event = {
        "date": event_date,
        "day": str(event_date.day),
        "title": title,
        "type": event_type,
        "scope": scope,
        "category": category,
        "is_holiday": is_holiday,
        "irrenunciable": irrenunciable,
    }
    event.update(extra)
    return event

def get_chilean_calendar(year):
    months = [{"name": month_name, "events": []} for month_name in MONTH_NAMES]

    for holiday in get_api_dates(year):
        try:
            holiday_date = date.fromisoformat(holiday["date"])
        except (KeyError, TypeError, ValueError):
            continue

        event = make_event(
            holiday_date,
            holiday.get("title"),
            holiday.get("type"),
            scope=holiday.get("scope"),
            category=holiday.get("category"),
            is_holiday=True,
            irrenunciable=holiday.get("irrenunciable", False),
        )
        months[holiday_date.month - 1]["events"].append(event)

    return months

def get_api_dates(year):
    cache_key = f"chilean-holidays:{year}"
    cached_dates = cache.get(cache_key)
    if cached_dates is not None:
        return cached_dates
    
    base_url = os.getenv("DJANGO_API_URL", "").strip()
    parsed_url = urlparse(base_url)
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        return []

    endpoint = urljoin(f"{base_url.rstrip('/')}/", f"dates/{year}")
    try:
        response = requests.get(endpoint, timeout=5)
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, KeyError, TypeError, ValueError):
        return []

    if not isinstance(data, list):
        return []

    cache.set(cache_key, data, timeout=86400)
    return data


# Backwards-compatible alias for callers using the original singular name.
get_api_date = get_api_dates


def get_google_redirect_uri(request):
    """Return the registered OAuth callback URL, or the local URL by default."""
    return os.getenv(
        "GOOGLE_CALENDAR_REDIRECT_URI",
        request.build_absolute_uri(reverse("google-calendar-callback")),
    )


def get_holiday_events(year):
    """Flatten the displayed calendar into the events that can be synced."""
    return [
        event
        for month in get_chilean_calendar(year)
        for event in month["events"]
        if event["is_holiday"] and isinstance(event["date"], date)
    ]


def google_calendar_connect(request):
    client_id = os.getenv("GOOGLE_CALENDAR_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CALENDAR_CLIENT_SECRET")
    if not client_id or not client_secret:
        messages.error(
            request,
            "La integración con Google Calendar aún no está configurada en el servidor.",
        )
        return redirect("home")

    state = secrets.token_urlsafe(32)
    action = request.GET.get("action", "sync")
    if action not in {"sync", "delete"}:
        action = "sync"
    request.session["google_calendar_oauth_state"] = state
    request.session["google_calendar_sync_year"] = date.today().year
    request.session["google_calendar_oauth_popup"] = request.GET.get("popup") == "1"
    request.session["google_calendar_action"] = action
    query = urlencode(
        {
            "client_id": client_id,
            "redirect_uri": get_google_redirect_uri(request),
            "response_type": "code",
            "scope": GOOGLE_CALENDAR_SCOPE,
            "state": state,
            "access_type": "online",
            "include_granted_scopes": "true",
            "prompt": "select_account",
        }
    )
    return redirect(f"{GOOGLE_AUTHORIZATION_URL}?{query}")


def google_calendar_callback(request):
    is_popup = request.session.pop("google_calendar_oauth_popup", False)

    def finish(message, level):
        if is_popup:
            return render(
                request,
                "google_calendar_popup_complete.html",
                {"notification_message": message, "notification_level": level},
            )
        getattr(messages, level)(request, message)
        return redirect("home")

    if request.GET.get("state") != request.session.pop("google_calendar_oauth_state", None):
        return finish("No se pudo validar la autorización de Google Calendar.", "error")

    if request.GET.get("error") or not request.GET.get("code"):
        return finish("La autorización de Google Calendar fue cancelada.", "error")

    token_response = requests.post(
        GOOGLE_TOKEN_URL,
        data={
            "code": request.GET["code"],
            "client_id": os.getenv("GOOGLE_CALENDAR_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_CALENDAR_CLIENT_SECRET"),
            "redirect_uri": get_google_redirect_uri(request),
            "grant_type": "authorization_code",
        },
        timeout=10,
    )
    try:
        token_response.raise_for_status()
        access_token = token_response.json()["access_token"]
    except (requests.RequestException, KeyError, TypeError, ValueError):
        return finish("Google no pudo completar la autorización. Inténtalo nuevamente.", "error")

    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        action = request.session.pop("google_calendar_action", "sync")
        if action == "delete":
            deleted = delete_synced_holidays_from_google_calendar(headers)
            return finish(f"Días eliminados: {deleted}.", "success")

        year = request.session.pop("google_calendar_sync_year", date.today().year)
        created, skipped = sync_holidays_to_google_calendar(year, headers)
    except requests.RequestException:
        return finish("No fue posible sincronizar los feriados con Google Calendar.", "error")

    return finish(
        f"Días añadidos: {created}. Ya existentes: {skipped}.",
        "success",
    )


def sync_holidays_to_google_calendar(year, headers):
    """Create missing Chilean holidays in the user's primary Google calendar."""
    start = date(year, 1, 1)
    end = date(year + 1, 1, 1)
    response = requests.get(
        GOOGLE_CALENDAR_EVENTS_URL,
        headers=headers,
        params={
            "timeMin": f"{start.isoformat()}T00:00:00Z",
            "timeMax": f"{end.isoformat()}T00:00:00Z",
            "singleEvents": "true",
            "privateExtendedProperty": "source=calendario-chile",
        },
        timeout=10,
    )
    response.raise_for_status()
    existing_ids = {
        item.get("extendedProperties", {}).get("private", {}).get("source_id")
        for item in response.json().get("items", [])
    }

    created = skipped = 0
    for event in get_holiday_events(year):
        source_id = f"{event['date'].isoformat()}:{event['title']}"
        if source_id in existing_ids:
            skipped += 1
            continue

        event_date = event["date"]
        payload = {
            "summary": event["title"],
            "description": "Feriado de Chile sincronizado desde Calendario de Chile.",
            "start": {"date": event_date.isoformat()},
            "end": {"date": (event_date + timedelta(days=1)).isoformat()},
            "extendedProperties": {
                "private": {"source": "calendario-chile", "source_id": source_id}
            },
        }
        create_response = requests.post(
            GOOGLE_CALENDAR_EVENTS_URL,
            headers=headers,
            json=payload,
            timeout=10,
        )
        create_response.raise_for_status()
        created += 1

    return created, skipped


def delete_synced_holidays_from_google_calendar(headers):
    """Delete only events created by this application from the primary calendar."""
    event_ids = []
    params = {
        "privateExtendedProperty": "source=calendario-chile",
        "maxResults": 2500,
    }
    while True:
        response = requests.get(
            GOOGLE_CALENDAR_EVENTS_URL,
            headers=headers,
            params=params,
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()

        event_ids.extend(
            event["id"] for event in payload.get("items", []) if event.get("id")
        )

        page_token = payload.get("nextPageToken")
        if not page_token:
            break
        params["pageToken"] = page_token

    for event_id in event_ids:
        delete_response = requests.delete(
            f"{GOOGLE_CALENDAR_EVENTS_URL}/{quote(event_id, safe='')}",
            headers=headers,
            timeout=10,
        )
        delete_response.raise_for_status()

    return len(event_ids)

def home(request):
    year = date.today().year
    months = get_chilean_calendar(year)
    api_url = os.getenv("DJANGO_API_URL", "").strip()
    is_api_configured = urlparse(api_url).scheme in {"http", "https"}
    return render(
        request,
        "index.html",
        {
            "months": months,
            "year": year,
            "calendar_unavailable": not is_api_configured,
        },
    )
