import sqlite3

def create_database():
    conn = sqlite3.connect('pose_estimations.db')
    c = conn.cursor()

    # Create users table
    c.execute('''
              CREATE TABLE users
              (mrn TEXT PRIMARY KEY,
              first_name TEXT,
              last_name TEXT,
              age INTEGER,
              sex TEXT,
              race TEXT,
              ethnicity TEXT)
              ''')

    # Insert some fake patient data
    c.execute('''
              INSERT INTO users (mrn, first_name, last_name, age, sex, race, ethnicity)
              VALUES 
              ('12345', 'John', 'Doe', 35, 'Male', 'White', 'Not Hispanic or Latino'),
              ('23456', 'Jane', 'Smith', 29, 'Female', 'Black or African American', 'Not Hispanic or Latino'),
              ('34567', 'Alice', 'Johnson', 42, 'Female', 'Asian', 'Hispanic or Latino'),
              ('45678', 'Bob', 'Brown', 50, 'Male', 'White', 'Hispanic or Latino')
              ''')

    # Create pose_estimations table
    c.execute('''
              CREATE TABLE pose_estimations
              (id INTEGER PRIMARY KEY AUTOINCREMENT,
              test_uuid TEXT,
              timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
              keypoints TEXT,
              angle REAL,
              exercise TEXT,
              count INTEGER,
              user_mrn TEXT,
              FOREIGN KEY (user_mrn) REFERENCES users(mrn))
              ''')

    conn.commit()
    conn.close()

if __name__ == '__main__':
    create_database()
