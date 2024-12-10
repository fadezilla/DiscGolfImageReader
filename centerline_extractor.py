import mysql.connector
import json
import io
from PIL import Image
import numpy as np

# Connect to the database
def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Code9856",
        database="discgolf"
    )

# Calculate midpoints and form a continuous centerline
def extract_centerline(flight_path_coords):
    midpoints = []
    
    # Loop through pairs of points and calculate midpoints
    for i in range(0, len(flight_path_coords) - 1, 2):
        x1, y1 = flight_path_coords[i]
        x2, y2 = flight_path_coords[i + 1]
        
        # Calculate midpoint
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        
        midpoints.append([mid_x, mid_y])

    return midpoints

# Fetch all discs with flight path coordinates
def fetch_all_discs_with_coords():
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, flight_path_coords FROM disc_flight_data WHERE flight_path_coords IS NOT NULL")
    discs = cursor.fetchall()
    cursor.close()
    conn.close()
    return discs

# Save the centerline back to the database
def save_centerline_to_db(disc_id, centerline_coords):
    conn = connect_db()
    cursor = conn.cursor()
    update_query = "UPDATE disc_flight_data SET flight_path_coords_centered = %s WHERE id = %s"
    cursor.execute(update_query, (json.dumps(centerline_coords), disc_id))
    conn.commit()
    cursor.close()
    conn.close()

# Process all discs, calculate centerline, and update the database
def process_and_save_centerlines():
    discs = fetch_all_discs_with_coords()
    
    for disc in discs:
        disc_id = disc['id']
        flight_path_coords = json.loads(disc['flight_path_coords'])
        
        # Calculate the centerline
        centerline_coords = extract_centerline(flight_path_coords)
        
        # Save centerline to the database
        save_centerline_to_db(disc_id, centerline_coords)
        print(f"Centerline for disc ID {disc_id} saved.")

if __name__ == "__main__":
    process_and_save_centerlines()
