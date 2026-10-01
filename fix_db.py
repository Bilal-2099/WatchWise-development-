import sqlite3

# Update this path if your database file is named differently or located elsewhere
DB_PATH = "watchwise.db" 

def fix_diary_rating_column():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("Migrating database...")

    # 1. Disable foreign keys temporarily for the migration
    cursor.execute("PRAGMA foreign_keys=OFF;")

    # 2. Create a new temporary table with the correct schema (rating allows NULL)
    cursor.execute("""
        CREATE TABLE diaryentry_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            tmdb_id INTEGER,
            media_type VARCHAR NOT NULL,
            rating FLOAT,  -- Now allows NULL!
            review_text VARCHAR,
            watch_date DATE,
            is_rewatch BOOLEAN,
            created_at DATETIME,
            FOREIGN KEY(user_id) REFERENCES user(id)
        );
    """)

    # 3. Copy existing data from the old table to the new table
    cursor.execute("""
        INSERT INTO diaryentry_new 
        SELECT id, user_id, tmdb_id, media_type, rating, review_text, watch_date, is_rewatch, created_at 
        FROM diaryentry;
    """)

    # 4. Drop the old table
    cursor.execute("DROP TABLE diaryentry;")

    # 5. Rename the new table to the original name
    cursor.execute("ALTER TABLE diaryentry_new RENAME TO diaryentry;")

    # 6. Re-enable foreign keys and commit
    cursor.execute("PRAGMA foreign_keys=ON;")
    conn.commit()
    conn.close()
    
    print("Database migration complete! Your data is safe.")

if __name__ == "__main__":
    fix_diary_rating_column()