from datetime import date
from django.core.cache import cache
from django.shortcuts import render
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

    for holiday in get_api_date(year):
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

def get_api_date(year):
    cache_key = f"chilean-holidays:{year}"
    cached_dates = cache.get(cache_key)
    if cached_dates is not None:
        return cached_dates
    
    url = os.getenv("DJANGO_API_URL")
    print(f"{url}/dates/{year}")
    try:
        response = requests.get(f"{url}/dates/{year}", timeout=5)
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, KeyError, TypeError, ValueError):
        return []

    cache.set(cache_key, data, timeout=86400)
    return data

def home(request):
    year = date.today().year
    months = get_chilean_calendar(year)
    return render(request, "index.html", {"months": months, "year": year})
