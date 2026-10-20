import sqlite3

DATABASE_NAME = "emergency.db"

connection = sqlite3.connect(DATABASE_NAME)
cursor = connection.cursor()

cursor.execute("DELETE FROM emergency_requests")
cursor.execute("DELETE FROM response_units")
cursor.execute("DELETE FROM hospitals")

cursor.execute("""
INSERT INTO response_units
(name, unit_type, location, status)
VALUES
('Ambulance 01', 'Medical', 'Location A', 'Available'),
('Ambulance 02', 'Medical', 'Location B', 'Busy'),
('Fire Unit 01', 'Fire', 'Location C', 'Available')
""")

cursor.execute("""
INSERT INTO hospitals
(name, location, emergency_services)
VALUES
('City Hospital', 'Location B', 'Available'),
('Central Medical Center', 'Location C', 'Available'),
('General Hospital', 'Location D', 'Available')
""")

connection.commit()
connection.close()

print("Sample data reset successfully!")