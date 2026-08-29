from datetime import date, timedelta

from django.shortcuts import render


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


def get_easter_sunday(year):
    """Return Easter Sunday for the Gregorian calendar."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def make_event(
    event_date,
    title,
    event_type,
    scope=None,
    category=None,
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
        "irrenunciable": irrenunciable,
    }
    event.update(extra)
    return event


def get_chilean_calendar(year):
    easter = get_easter_sunday(year)
    events = [
        make_event(
            date(year, 1, 1),
            "Año Nuevo",
            "Feriado",
            "Nacional",
            "Civil",
            True,
        ),
        make_event(
            date(year, 2, 12),
            "Fundación de Santiago",
            "Historia",
            category="Histórica",
        ),
        make_event(
            date(year, 2, 14),
            "Día del Amor y la Amistad",
            "Cultural",
            category="Cultural",
        ),
        make_event(
            date(year, 3, 8),
            "Día Internacional de la Mujer",
            "Conmemoración",
            category="Internacional",
        ),
        make_event(
            date(year, 3, 20),
            "Inicio del otoño",
            "Estación",
            category="Astronómica",
        ),
        make_event(
            easter - timedelta(days=2),
            "Viernes Santo",
            "Feriado",
            "Nacional",
            "Religioso",
        ),
        make_event(
            easter - timedelta(days=1),
            "Sábado Santo",
            "Feriado",
            "Nacional",
            "Religioso",
        ),
        make_event(
            date(year, 4, 27),
            "Día de Carabineros de Chile",
            "Conmemoración",
            category="Institucional",
        ),
        make_event(
            date(year, 5, 1),
            "Día Nacional del Trabajo",
            "Feriado",
            "Nacional",
            "Civil",
            True,
        ),
        make_event(
            date(year, 5, 21),
            "Día de las Glorias Navales",
            "Feriado",
            "Nacional",
            "Histórica",
        ),
        make_event(
            date(year, 6, 7),
            "Asalto y Toma del Morro de Arica",
            "Feriado",
            "Regional",
            "Histórica",
            region="Región de Arica y Parinacota",
        ),
        make_event(
            date(year, 6, 21),
            "Día Nacional de los Pueblos Indígenas",
            "Feriado",
            "Nacional",
            "Cultural",
        ),
        make_event(
            move_to_monday_if_required(date(year, 6, 29)),
            "San Pedro y San Pablo",
            "Feriado",
            "Nacional",
            "Religioso",
        ),
        make_event(
            date(year, 7, 9),
            "Día Nacional de la Bandera",
            "Conmemoración",
            category="Histórica",
        ),
        make_event(
            date(year, 7, 16),
            "Día de la Virgen del Carmen",
            "Feriado",
            "Nacional",
            "Religioso",
        ),
        make_event(
            date(year, 8, 10),
            "Día del Minero",
            "Conmemoración",
            category="Laboral",
        ),
        make_event(
            date(year, 8, 15),
            "Asunción de la Virgen",
            "Feriado",
            "Nacional",
            "Religioso",
        ),
        make_event(
            date(year, 8, 20),
            "Natalicio de Bernardo O'Higgins",
            "Feriado",
            "Comunal",
            "Histórica",
            region="Región de Ñuble",
            communes=[
                "Chillán",
                "Chillán Viejo",
            ],
        ),
        make_event(
            date(year, 9, 18),
            "Independencia Nacional",
            "Feriado",
            "Nacional",
            "Fiestas Patrias",
            True,
        ),
        make_event(
            date(year, 9, 19),
            "Día de las Glorias del Ejército",
            "Feriado",
            "Nacional",
            "Fiestas Patrias",
            True,
        ),
        make_event(
            date(year, 10, 4),
            "Día de la Música y de los Músicos Chilenos",
            "Conmemoración",
            category="Cultural",
        ),
        make_event(
            move_to_monday_if_required(date(year, 10, 12)),
            "Encuentro de Dos Mundos",
            "Feriado",
            "Nacional",
            "Histórica",
        ),
        make_event(
            get_evangelical_holiday(year),
            "Día Nacional de las Iglesias Evangélicas y Protestantes",
            "Feriado",
            "Nacional",
            "Religioso",
        ),
        make_event(
            date(year, 11, 1),
            "Día de Todos los Santos",
            "Feriado",
            "Nacional",
            "Religioso",
        ),
        make_event(
            date(year, 12, 8),
            "Inmaculada Concepción",
            "Feriado",
            "Nacional",
            "Religioso",
        ),
        make_event(
            date(year, 12, 25),
            "Navidad",
            "Feriado",
            "Nacional",
            "Religioso",
            True,
        ),
        make_event(
            date(year, 12, 31),
            "Víspera de Año Nuevo",
            "Cultural",
            category="Cultural",
        ),
    ]

    months = [{"name": month_name, "events": []} for month_name in MONTH_NAMES]
    for event in sorted(events, key=lambda item: item["date"]):
        month_index = event["date"].month - 1
        event.pop("date")
        months[month_index]["events"].append(event)

    return months

def move_to_monday_if_required(event_date):
    weekday = event_date.weekday()

    if weekday in (1, 2, 3):
        return event_date - timedelta(days=weekday)

    if weekday == 4:
        return event_date + timedelta(days=3)

    return event_date

def get_evangelical_holiday(year):
    holiday = date(year, 10, 31)

    if holiday.weekday() == 1:
        return holiday - timedelta(days=4)

    if holiday.weekday() == 2:
        return holiday + timedelta(days=2)

    return holiday

def home(request):
    year = date.today().year
    months = get_chilean_calendar(year)
    return render(request, "index.html", {"months": months, "year": year})
