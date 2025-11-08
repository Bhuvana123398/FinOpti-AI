import sqlite3
from sqlite3 import Error

DATABASE_FILE = "users.db"

def create_connection():
    """Create a database connection to a SQLite database."""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        return conn
    except Error as e:
        print(e)
    return conn

def setup_database():
    """Create the users table if it doesn't exist."""
    conn = create_connection()
    if conn is not None:
        try:
            c = conn.cursor()
            c.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL
                );
            """)
            conn.close()
        except Error as e:
            print(e)
    else:
        print("Error! cannot create the database connection.")

def add_user(username, password_hash):
    """Add a new user to the users table. Manages its own connection."""
    conn = create_connection()
    sql = ''' INSERT INTO users(username,password_hash)
              VALUES(?,?) '''
    cur = conn.cursor()
    try:
        cur.execute(sql, (username, password_hash))
        conn.commit()
        user_id = cur.lastrowid
    except sqlite3.IntegrityError:
        user_id = None # Username already exists
    finally:
        conn.close()
    return user_id

def check_user(username):
    """Query user by username to get their password hash. Manages its own connection."""
    conn = create_connection()
    password_hash = None
    try:
        cur = conn.cursor()
        cur.execute("SELECT password_hash FROM users WHERE username=?", (username,))
        row = cur.fetchone()
        if row:
            password_hash = row[0]
    except Error as e:
        print(e)
    finally:
        conn.close()
    return password_hash