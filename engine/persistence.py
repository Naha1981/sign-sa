import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'user_stats.db')

class PersistenceManager:
    def __init__(self):
        self._ensure_db_dir()
        self.conn = sqlite3.connect(DB_PATH)
        self._init_schema()

    def _ensure_db_dir(self):
        db_dir = os.path.dirname(DB_PATH)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)

    def _init_schema(self):
        cursor = self.conn.cursor()
        
        # User Mastery Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mastery (
                sign_name TEXT PRIMARY KEY,
                category TEXT,
                level INTEGER DEFAULT 0,  -- 0: New, 1: Learning, 2: Mastered
                last_practiced TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Feedback Cache Table (for offline feedback submission)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feedback_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sign_name TEXT,
                province TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                synced BOOLEAN DEFAULT 0
            )
        ''')
        
        self.conn.commit()

    def update_mastery(self, sign_name, level):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO mastery (sign_name, level, last_practiced)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(sign_name) DO UPDATE SET
                level = excluded.level,
                last_practiced = CURRENT_TIMESTAMP
        ''', (sign_name, level))
        self.conn.commit()

    def get_progress(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT category, COUNT(*) FROM mastery WHERE level > 0 GROUP BY category")
        return cursor.fetchall()
        
    def queue_feedback(self, sign, province, desc):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO feedback_queue (sign_name, province, description)
            VALUES (?, ?, ?)
        ''', (sign, province, desc))
        self.conn.commit()
    
    def get_unsynced_feedback(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM feedback_queue WHERE synced = 0")
        return cursor.fetchall()

    def close(self):
        self.conn.close()

if __name__ == "__main__":
    pm = PersistenceManager()
    pm.update_mastery("HELLO", 1)
    print("Updated hello.")
    pm.queue_feedback("BUS", "Gauteng", "Hand moves twice")
    print("Queued feedback.")
    print(pm.get_unsynced_feedback())
    pm.close()
