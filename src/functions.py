import os
import pyodbc
import requests
from dotenv import load_dotenv

load_dotenv(override=True)

server = os.getenv('SERVER')
database = os.getenv('DATABASE')
username = os.getenv('DB_USERNAME') or os.getenv('USERNAME')
password = os.getenv('DB_PASSWORD') or os.getenv('PASSWORD')

CONNECTION_STRING = (
    f'DRIVER={{ODBC Driver 18 for SQL Server}};'
    f'SERVER={server};DATABASE={database};UID={username};PWD={password};'
    'TrustServerCertificate=yes;Encrypt=yes'
)

DATA_SOURCES = {
    'films': 'https://swapi.info/api/films',
    'people': 'https://swapi.info/api/people',
    'planets': 'https://swapi.info/api/planets',
    'species': 'https://swapi.info/api/species',
    'vehicles': 'https://swapi.info/api/vehicles',
    'starships': 'https://swapi.info/api/starships',
}

TABLE_SCHEMAS = {
    'Films': {
        'create': '''
            title NVARCHAR(255) PRIMARY KEY,
            director NVARCHAR(255),
            release_date NVARCHAR(50)
        ''',
        'fields': [
            ('title', ['title', 'name']),
            ('director', ['director']),
            ('release_date', ['release_date', 'release']),
        ],
    },
    'People': {
        'create': '''
            name NVARCHAR(255) PRIMARY KEY,
            height NVARCHAR(50),
            mass NVARCHAR(50),
            gender NVARCHAR(50)
        ''',
        'fields': [
            ('name', ['name']),
            ('height', ['height']),
            ('mass', ['mass']),
            ('gender', ['gender']),
        ],
    },
    'Planets': {
        'create': 'name NVARCHAR(255) PRIMARY KEY',
        'fields': [('name', ['name'])],
    },
    'Species': {
        'create': 'name NVARCHAR(255) PRIMARY KEY',
        'fields': [('name', ['name'])],
    },
    'Vehicles': {
        'create': 'name NVARCHAR(255) PRIMARY KEY',
        'fields': [('name', ['name'])],
    },
    'Starships': {
        'create': 'name NVARCHAR(255) PRIMARY KEY',
        'fields': [('name', ['name'])],
    },
    'Users': {
        'create': '''
            name NVARCHAR(255),
            surname NVARCHAR(255),
            email NVARCHAR(255),
            country NVARCHAR(255),
            city NVARCHAR(255),
            salary DECIMAL(18,2)
        ''',
        'fields': [
            ('name', ['name']),
        ],
    },
}

CATEGORY_TABLES = {
    'films': 'Films',
    'people': 'People',
    'planets': 'Planets',
    'species': 'Species',
    'vehicles': 'Vehicles',
    'starships': 'Starships',
}

def prompt_menu():
    print('\nSWAPI Importer Menu:')
    print('1. Import films, people, planets, species, vehicles, starships')
    print('2. Show data for films, people, planets, species, vehicles, starships')
    print('3. Exit')


def prompt_table_choice():
    print('\nSelect table to show:')
    for index, table in enumerate(TABLES, start=1):
        print(f' {index}. {table}')
    print(f' {len(TABLES) + 1}. Back')

    while True:
        choice = input('Enter option: ').strip()
        if not choice.isdigit():
            print('Please enter a number.')
            continue

        choice = int(choice)
        if 1 <= choice <= len(TABLES):
            return TABLES[choice - 1]
        if choice == len(TABLES) + 1:
            return None
        print('Unknown option. Try again.')

def _fetch_swapi(url):
    """Generator that fetches paginated SWAPI-like endpoints and yields results."""
    while url:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        if isinstance(data, list):
            for item in data:
                yield item
            return

        if isinstance(data, dict):
            results = (
                data.get('results')
                or data.get('docs')
                or data.get('films')
                or data.get('people')
                or data.get('items')
                or data.get('data')
            )

            if isinstance(results, list):
                for item in results:
                    yield item
            elif isinstance(data, dict) and not results:
                yield data

            url = data.get('next') or data.get('nextPage') or data.get('next_url')
            continue

        break


def _ensure_table(conn, table_name):
    if table_name not in TABLE_SCHEMAS:
        raise ValueError(f'Unknown table: {table_name}')

    cursor = conn.cursor()
    cursor.execute(f"""
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = '{table_name}')
        CREATE TABLE {table_name} (
            {TABLE_SCHEMAS[table_name]['create']}
        )
    """)
    conn.commit()


def ensure_all_tables(conn):
    for table_name in TABLE_SCHEMAS:
        _ensure_table(conn, table_name)


def _get_value(item, keys):
    for key in keys:
        value = item.get(key)
        if value not in (None, ''):
            return value
    return None


def _import_category(table_name, url):
    if table_name not in TABLE_SCHEMAS:
        raise ValueError(f'Unknown import table: {table_name}')

    cursor = None
    added = 0
    with pyodbc.connect(CONNECTION_STRING) as conn:
        _ensure_table(conn, table_name)
        cursor = conn.cursor()

        fields = TABLE_SCHEMAS[table_name]['fields']
        columns = [name for name, _ in fields]
        placeholders = ', '.join(['?'] * len(columns))
        insert_sql = (
            f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
        )

        for item in _fetch_swapi(url):
            if not isinstance(item, dict):
                continue

            values = [_get_value(item, keys) for _, keys in fields]
            if not values[0]:
                continue

            cursor.execute(
                f"SELECT 1 FROM {table_name} WHERE {columns[0]} = ?",
                (values[0],),
            )
            if cursor.fetchone():
                continue

            cursor.execute(insert_sql, values)
            added += 1

        conn.commit()

    print(f'Imported {table_name}: {added}')


def import_films(url=None):
    _import_category('Films', url or DATA_SOURCES['films'])


def import_people(url=None):
    _import_category('People', url or DATA_SOURCES['people'])


def import_planets(url=None):
    _import_category('Planets', url or DATA_SOURCES['planets'])


def import_species(url=None):
    _import_category('Species', url or DATA_SOURCES['species'])


def import_vehicles(url=None):
    _import_category('Vehicles', url or DATA_SOURCES['vehicles'])


def import_starships(url=None):
    _import_category('Starships', url or DATA_SOURCES['starships'])


def import_all():
    import_films()
    import_people()
    import_planets()
    import_species()
    import_vehicles()
    import_starships()


def show_table(table_name):
    if table_name not in TABLE_SCHEMAS:
        print(f'Unknown table: {table_name}')
        return

    order_clause = ''
    if table_name == 'People':
        order_clause = ' ORDER BY gender, name'

    try:
        with pyodbc.connect(CONNECTION_STRING) as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {table_name}{order_clause}")
            rows = cursor.fetchall()
            if not rows:
                print(f'No rows in {table_name}')
                return

            columns = [column[0] for column in cursor.description]
            print(' | '.join(columns))
            print('-' * (len(columns) * 15))
            for row in rows:
                print(' | '.join(str(value) if value is not None else '' for value in row))

    except Exception as e:
        print(f'Error reading {table_name}: {e}')


def get_all_users():
    try:
        with pyodbc.connect(CONNECTION_STRING) as conn:
            _ensure_table(conn, 'Users')
            cursor = conn.cursor()
            cursor.execute(
                'SELECT name, surname, email, country, city, salary FROM Users'
            )
            rows = cursor.fetchall()
            if not rows:
                print('No rows in Users')
                return
            for row in rows:
                print(row)

    except Exception as e:
        print(f'Error: {e}')
