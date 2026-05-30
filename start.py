import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
import functions

TABLES = [
    'Films',
    'People',
    'Planets',
    'Species',
    'Vehicles',
    'Starships',
]

IMPORT_FUNCTIONS = {
    'Films': functions.import_films,
    'People': functions.import_people,
    'Planets': functions.import_planets,
    'Species': functions.import_species,
    'Vehicles': functions.import_vehicles,
    'Starships': functions.import_starships,
}

SHOW_FUNCTIONS = {
    'Films': lambda: functions.show_table('Films'),
    'People': lambda: functions.show_table('People'),
    'Planets': lambda: functions.show_table('Planets'),
    'Species': lambda: functions.show_table('Species'),
    'Vehicles': lambda: functions.show_table('Vehicles'),
    'Starships': lambda: functions.show_table('Starships'),
}


def prompt_menu():
    print('\nSWAPI Importer Menu:')
    for index, table in enumerate(TABLES, start=1):
        print(f' {index}. Import {table.lower()}')
    for index, table in enumerate(TABLES, start=len(TABLES) + 1):
        print(f' {index}. Show {table.lower()}')
    print(f' {len(TABLES) * 2 + 1}. Exit')


def main():
    while True:
        prompt_menu()
        choice = input('Enter option: ').strip()

        if not choice.isdigit():
            print('Please enter a number.')
            continue

        choice = int(choice)
        if 1 <= choice <= len(TABLES):
            table_name = TABLES[choice - 1]
            IMPORT_FUNCTIONS[table_name]()
        elif len(TABLES) < choice <= len(TABLES) * 2:
            table_name = TABLES[choice - len(TABLES) - 1]
            SHOW_FUNCTIONS[table_name]()
        elif choice == len(TABLES) * 2 + 1:
            print('Goodbye!')
            break
        else:
            print(f'Unknown option. Please select 1 through {len(TABLES) * 2 + 1}.')


if __name__ == '__main__':
    main()
