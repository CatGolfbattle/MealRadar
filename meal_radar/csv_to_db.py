import sqlite3
import os
import csv

# Norāda failu atrašanās vietas
base_directory = os.path.dirname(__file__)  # Vieta, kur atrodas mape ar Python skriptu
csv_directory = os.path.join(base_directory, 'csv')  # Vieta, kur atrodas mape "csv"
db_name = os.path.join(base_directory, 'csv_database.db')  # Norāda vietu un izveido datubāzi ar nosaukumu "csv_database.db"

# Funkcija, kura norādītajā datubāzē izveido tabulas no csv failiem
def csv_to_sqlite(db_name, csv_file, table_name):
    # Izveido savienojumu ar SQLite datubāzi
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    # Nolasa csv failu
    with open(csv_file, 'r', encoding='ISO-8859-1') as file:  # Norāda kodējuma veidu, lai dati parādītos korekti
        reader = csv.reader(file, delimiter=';')  # Semikols lietots kā kolonu atdalītājs
        headers = next(reader)  # Pirmo rindu norāda kā kolonu virsrakstus
        
        # Izveido datubāzes tabulu
        columns = ', '.join([f'"{header}" TEXT' for header in headers])
        cursor.execute(f'CREATE TABLE IF NOT EXISTS "{table_name}" ({columns})')
        
        # Ievieto datu rindas no csv faila datubāzes tabulā
        for row in reader:
            placeholders = ', '.join(['?' for _ in headers])
            cursor.execute(f'INSERT INTO "{table_name}" VALUES ({placeholders})', row)
    
    # Iesniedz/veic izmaiņas datubāzē un aizver datubāzes savienojumu
    conn.commit()
    conn.close()

# Katram csv failam, kas atrodas norādītajā mapē, izsauc funkciju csv_to_sqlite
for file_name in os.listdir(csv_directory):
    if file_name.endswith('.csv'):
        file_path = os.path.join(csv_directory, file_name)
        table_name = os.path.splitext(file_name)[0]  # Norāda, ka faila nosaukums bez paplašinājuma jālieto kā tabulas nosaukums
        csv_to_sqlite(db_name, file_path, table_name)

print(f"Datubāze '{db_name}' izveidota veiksmīgi.")
