import sqlite3

DATABASE_NAME = "emergency.db"


def get_connection():
    return sqlite3.connect(DATABASE_NAME)


connection = get_connection()
cursor = connection.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS emergency_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    location TEXT NOT NULL,
    emergency_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    status TEXT NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS response_units (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    unit_type TEXT NOT NULL,
    location TEXT NOT NULL,
    status TEXT NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS hospitals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    location TEXT NOT NULL,
    emergency_services TEXT NOT NULL
)
""")

connection.commit()
connection.close()


def get_response_units():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
    SELECT * FROM response_units
    ORDER BY id
    """)

    units = cursor.fetchall()

    connection.close()

    return units


def get_available_response_units():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
    SELECT * FROM response_units
    WHERE status = 'Available'
    ORDER BY id
    """)

    units = cursor.fetchall()

    connection.close()

    return units


def get_hospitals():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
    SELECT * FROM hospitals
    ORDER BY id
    """)

    hospitals = cursor.fetchall()

    connection.close()

    return hospitals


def add_emergency_request(
    location,
    emergency_type,
    severity
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
    INSERT INTO emergency_requests
    (location, emergency_type, severity, status)
    VALUES (?, ?, ?, ?)
    """, (
        location,
        emergency_type,
        severity,
        "Pending"
    ))

    emergency_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return emergency_id


def get_emergency_requests():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
    SELECT * FROM emergency_requests
    ORDER BY id DESC
    """)

    emergencies = cursor.fetchall()

    connection.close()

    return emergencies


def update_unit_status(
    unit_id,
    status
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
    UPDATE response_units
    SET status = ?
    WHERE id = ?
    """, (
        status,
        unit_id
    ))

    connection.commit()
    connection.close()


def update_emergency_status(
    emergency_id,
    status
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
    UPDATE emergency_requests
    SET status = ?
    WHERE id = ?
    """, (
        status,
        emergency_id
    ))

    connection.commit()
    connection.close()