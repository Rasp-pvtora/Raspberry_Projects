import sqlite3
from datetime import datetime
from cryptography.fernet import Fernet
import config

fernet = Fernet(config.ENCRYPTION_KEY)

def init_db():
    conn = sqlite3.connect(config.DB_FILE)
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS vehicles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        plate_number TEXT UNIQUE,
        car_type TEXT,
        color TEXT,
        first_seen DATETIME,
        last_seen DATETIME,
        owner_name TEXT,  -- Encrypted
        owner_surname TEXT,  -- Encrypted
        owner_address TEXT   -- Encrypted
    )
    ''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vehicle_id INTEGER,
        entry_time DATETIME,
        exit_time DATETIME,  -- For future duration
        FOREIGN KEY (vehicle_id) REFERENCES vehicles(id)
    )
    ''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS watchlist (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        plate_number TEXT UNIQUE
    )
    ''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        plate_number TEXT,
        timestamp DATETIME,
        location TEXT
    )
    ''')
    conn.commit()
    return conn

def encrypt(data):
    return fernet.encrypt(data.encode()).decode() if data else None

def decrypt(data):
    return fernet.decrypt(data.encode()).decode() if data else None

def search_existing_plate(conn, plate_number):
    cur = conn.cursor()
    cur.execute("SELECT * FROM vehicles WHERE plate_number = ?", (plate_number,))
    row = cur.fetchone()
    if row:
        return {
            'id': row[0],
            'plate_number': row[1],
            'car_type': row[2],
            'color': row[3],
            'owner_name': decrypt(row[6]),  # GDPR: Decrypt on read
            'owner_surname': decrypt(row[7]),
            'owner_address': decrypt(row[8])
        }
    return None

def add_new_plate(conn, plate_number, car_type, color):
    cur = conn.cursor()
    now = datetime.now()
    cur.execute("""
        INSERT INTO vehicles (plate_number, car_type, color, first_seen, last_seen)
        VALUES (?, ?, ?, ?, ?)
    """, (plate_number, car_type, color, now, now))
    conn.commit()
    return cur.lastrowid

def update_owner_details(conn, plate_number, name, surname, address):
    cur = conn.cursor()
    cur.execute("""
        UPDATE vehicles SET 
        owner_name = ?, owner_surname = ?, owner_address = ?
        WHERE plate_number = ?
    """, (encrypt(name), encrypt(surname), encrypt(address), plate_number))
    conn.commit()

def log_vehicle_entry(conn, vehicle_id, entry_time, is_exit=False):
    cur = conn.cursor()
    if is_exit:
        # Nice-to-have: Update last entry with exit time for duration
        cur.execute("""
            UPDATE entries SET exit_time = ? 
            WHERE vehicle_id = ? AND exit_time IS NULL
            ORDER BY entry_time DESC LIMIT 1
        """, (entry_time, vehicle_id))
    else:
        cur.execute("INSERT INTO entries (vehicle_id, entry_time) VALUES (?, ?)", (vehicle_id, entry_time))
    cur.execute("UPDATE vehicles SET last_seen = ? WHERE id = ?", (entry_time, vehicle_id))
    conn.commit()

# Add more: e.g., add_to_watchlist, etc.
def add_to_watchlist(conn, plate_number):
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO watchlist (plate_number) VALUES (?)", (plate_number,))
    conn.commit()
