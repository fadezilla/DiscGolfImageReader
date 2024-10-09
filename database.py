import mysql.connector

def connect_db():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Code9856",
        database="discgolf"
    )
    return conn

def fetch_single_disc_image(disc_id=308):  # Default disc ID is 233
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT flight_path FROM discs WHERE id = %s", (disc_id,))
    disc = cursor.fetchone()
    cursor.close()
    conn.close()
    return disc