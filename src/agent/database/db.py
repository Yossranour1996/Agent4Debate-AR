import os
import sqlite3
from typing import Optional
from datetime import datetime

def init_db(force: bool = False):
    db_name = ".cache/search.db"
    
    # Ensure .cache directory exists
    os.makedirs(".cache", exist_ok=True)

    # If force is True, delete existing db file to reset
    if force and os.path.exists(db_name):
        print("Removing existing database for reinitialization.")
        os.remove(db_name)
    
    # Connect to database and create cursor
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    # Create table if it does not exist
    print("Creating queries table if it does not exist.")
    c.execute('''CREATE TABLE IF NOT EXISTS queries
                 (query TEXT PRIMARY KEY, 
                  answer TEXT, 
                  created_at TIMESTAMP, 
                  updated_at TIMESTAMP)''')
    
    # Insert default data if forcing a reset
    if force:
        current_time = datetime.now().isoformat()
        print("Inserting default data into queries table.")
        c.execute("INSERT OR REPLACE INTO queries VALUES (?, ?, ?, ?)", 
                  ("What is the purpose of this database?", 
                   "To cache query results for faster retrieval.",
                   current_time,
                   current_time))
        print("Database has been initialized with default data.")
        
    # Commit and close the database
    conn.commit()
    conn.close()
    print("Database setup complete.")

def save_query(query: str, answer: str):
    conn = sqlite3.connect('.cache/search.db')
    c = conn.cursor()
    current_time = datetime.now().isoformat()
    
    # Check if the query already exists
    c.execute("SELECT created_at FROM queries WHERE query = ?", (query,))
    existing = c.fetchone()
    
    if existing:
        # Update existing query
        print(f"Updating existing query in the database: {query}")
        c.execute("UPDATE queries SET answer = ?, updated_at = ? WHERE query = ?", 
                  (answer, current_time, query))
    else:
        # Insert new query
        print(f"Inserting new query into the database: {query}")
        c.execute("INSERT INTO queries VALUES (?, ?, ?, ?)", 
                  (query, answer, current_time, current_time))
    
    conn.commit()
    conn.close()

def get_cached_answer(query: str) -> Optional[tuple]:
    conn = sqlite3.connect('.cache/search.db')
    c = conn.cursor()
    print(f"Retrieving cached answer for query: {query}")
    c.execute("SELECT answer, created_at, updated_at FROM queries WHERE query = ?", (query,))
    result = c.fetchone()
    conn.close()
    return result if result else None

def remove_query(query: str) -> bool:
    conn = sqlite3.connect('.cache/search.db')
    c = conn.cursor()
    
    try:
        print(f"Attempting to remove query from database: {query}")
        c.execute("DELETE FROM queries WHERE query = ?", (query,))
        conn.commit()
        
        if c.rowcount > 0:
            print(f"Query '{query}' has been removed from the database.")
            return True
        else:
            print(f"Query '{query}' was not found in the database.")
            return False
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        return False
    finally:
        conn.close()

# Force initialize the database to ensure the structure is correct
init_db(force=True)
