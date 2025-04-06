import sqlite3
import os

# Norāda datubāzes atrašanās vietu
base_directory = os.path.dirname(__file__)  # Vieta, kur atrodas mape ar Python skriptu
db_name = os.path.join(base_directory, 'csv_database.db')  # Norāda vietu, kur atrodas datubāze "csv_database.db"

# Izveido savienojumu ar SQLite datubāzi
conn = sqlite3.connect(db_name)
cursor = conn.cursor()

# Izveido SQL komandu jaunas skata/ tabulas izveidošanai, apvienojot citas tabulas
def create_view(cursor):
    try:
        # Izdzēš iepriekš izveidoto skatu
        cursor.execute('DROP VIEW IF EXISTS MealRadarTable;')
        
        # Izveido jaunu skatu
        cursor.execute('''
        CREATE VIEW MealRadarTable AS
        SELECT 
            food.foodid,
            foodname_en.foodname,
            COALESCE(MAX(CASE WHEN component_value.eufdname = 'ENERC' THEN component_value.bestloc END), 0) AS ENERC,
            COALESCE(MAX(CASE WHEN component_value.eufdname = 'SUGAR' THEN component_value.bestloc END), 0) AS SUGAR,
            COALESCE(MAX(CASE WHEN component_value.eufdname = 'FAT' THEN component_value.bestloc END), 0) AS FAT,
            COALESCE(MAX(CASE WHEN component_value.eufdname = 'FASAT' THEN component_value.bestloc END), 0) AS FASAT,
            COALESCE(MAX(CASE WHEN component_value.eufdname = 'NACL' THEN component_value.bestloc END), 0) AS NACL
        FROM 
            food
        LEFT JOIN 
            foodname_en
        ON 
            food.foodid = foodname_en.foodid
        LEFT JOIN
            component_value
        ON
            food.foodid = component_value.foodid
        GROUP BY 
            food.foodid, foodname_en.foodname;

        ''')
        print("Jaunā tabula 'MealRadarTable' veiksmīgi izveidota.")
    except sqlite3.Error as e:
        print("Radās kļūda, veidojot jauno tabulu:", e)

# Izpilda darbību - izveido vai aizvieto skatu
create_view(cursor)

# Iesniedz/veic izmaiņas datubāzē un aizver datubāzes savienojumu
conn.commit()
conn.close()
