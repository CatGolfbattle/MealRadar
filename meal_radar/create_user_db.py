import sqlite3
import bcrypt

# Izveido savienojumu ar SQLite datubāzi
conn = sqlite3.connect('users.db')
cursor = conn.cursor()

# Izveido datubāzi users, ja tāda neeksistē
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
);
''')

def add_user(username, password):
    """
    Funkcija, kas pievieno lietotāju ar šifrētu paroli datubāzē
    """
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
    conn.commit()

# Pievieno lietotāju testēšanai
add_user('user1', 'password1')

# Aizver datubāzes savienojumu
conn.close()
   