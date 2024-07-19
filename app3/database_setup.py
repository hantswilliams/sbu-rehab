import sqlite3

def create_database():
    conn = sqlite3.connect('pose_estimations.db')
    c = conn.cursor()
    c.execute('''
              CREATE TABLE pose_estimations
              (id INTEGER PRIMARY KEY AUTOINCREMENT,
              timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
              keypoints TEXT,
              angle REAL,
              exercise TEXT,
              count INTEGER)
              ''')
    conn.commit()
    conn.close()

if __name__ == '__main__':
    create_database()
