# Calendario de Chile

Aplicacion web hecha con Django que muestra un calendario anual de fechas importantes de Chile. Incluye feriados, conmemoraciones, hitos historicos y celebraciones culturales, agrupados por mes.

## Que Hace

- Muestra los eventos del año actual en una vista web.
- Agrupa las fechas por mes.
- Destaca los feriados irrenunciables con una clase CSS especial.
- Permite filtrar eventos desde la interfaz por tipo: todos, feriados, historia, cultura y conmemoraciones.
- Calcula automaticamente los feriados moviles asociados a Semana Santa segun el año.

## Como Funciona

La vista principal esta en `core/views.py`.

La funcion `get_chilean_calendar(year)` recibe un año y devuelve una lista de meses con esta estructura:

```python
[
    {
        "name": "Enero",
        "events": [
            {
                "day": "1",
                "title": "Año Nuevo",
                "type": "Feriado",
                "scope": "Nacional",
                "category": "Civil",
                "irrenunciable": True,
            },
        ],
    },
]
```

Los feriados fijos se crean con fechas del año recibido. Los feriados moviles `Viernes Santo` y `Sabado Santo` se calculan a partir de la fecha de Pascua usando `get_easter_sunday(year)`.

El template principal esta en `core/templates/index.html` y consume la variable `months` enviada desde la vista `home`.

## Alcance

Este proyecto esta pensado como una aplicacion simple de calendario chileno para consulta visual.

Incluye:

- Fechas fijas relevantes.
- Feriados nacionales, regionales y comunales definidos en el codigo.
- Calculo automatico de Semana Santa.
- Marcado visual para feriados irrenunciables.

No incluye por ahora:

- Panel de administracion para editar fechas.
- Base de datos con eventos.
- API publica.
- Seleccion de año desde la interfaz.
- Validacion automatica contra fuentes oficiales externas.
- Reglas especiales de traslado de feriados.

## Requisitos

- Python 3.11 o superior.
- Django 5.2.17.

Las dependencias estan declaradas en `requirements.txt`.

## Instalacion

Clonar el repositorio:

```bash
git clone <url-del-repositorio>
cd CalendarioChile
```

Crear un entorno virtual:

```bash
python -m venv .venv
```

Activar el entorno virtual en Windows PowerShell:

```powershell
.venv\Scripts\activate
```

Si el entorno fue creado con estructura tipo Unix, por ejemplo usando MSYS o Git Bash:

```bash
source .venv/bin/activate
```

Instalar dependencias:

```bash
pip install -r requirements.txt
```

## Ejecucion

Aplicar migraciones iniciales de Django:

```bash
python manage.py migrate
```

Levantar el servidor de desarrollo:

```bash
python manage.py runserver
```

Abrir en el navegador:

```txt
http://127.0.0.1:8000/
```

## Estructura del Proyecto

```txt
CalendarioChile/
|-- manage.py
|-- requirements.txt
|-- README.md
|-- .gitignore
|-- mysite/
|   |-- settings.py
|   |-- urls.py
|   |-- asgi.py
|   `-- wsgi.py
`-- core/
    |-- views.py
    |-- urls.py
    |-- models.py
    |-- admin.py
    |-- apps.py
    |-- tests.py
    |-- migrations/
    |   `-- __init__.py
    `-- templates/
        `-- index.html
```

## Archivos Importantes

- `core/views.py`: contiene la funcion `get_chilean_calendar(year)` y la vista principal.
- `core/templates/index.html`: contiene el HTML, CSS y JavaScript de la interfaz.
- `core/urls.py`: define la ruta principal de la app.
- `mysite/urls.py`: conecta la app `core` con el proyecto Django.
- `requirements.txt`: lista las dependencias necesarias.

## Git

No se debe subir el entorno virtual ni archivos generados localmente.

El `.gitignore` deberia incluir:

```gitignore
.venv/
venv/
env/
__pycache__/
*.pyc
db.sqlite3
.env
```

## Notas de Desarrollo

Para agregar una nueva fecha, editar `get_chilean_calendar(year)` en `core/views.py` y agregar un nuevo `make_event(...)`.

Ejemplo:

```python
make_event(
    date(year, 9, 18),
    "Independencia Nacional",
    "Feriado",
    "Nacional",
    "Fiestas Patrias",
    True,
)
```

El ultimo valor (`True` o `False`) indica si el feriado es irrenunciable.
