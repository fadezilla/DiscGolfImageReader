import mysql.connector
import json
import cv2
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import io

# Connect to the database
def connect_db():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Code9856",
        database="discgolf"
    )
    return conn

# Fetch flight path coordinates and image for a specific disc
def fetch_flight_path_data(disc_id):
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT flight_path_coords, flight_data_image FROM disc_flight_data WHERE id = %s", (disc_id,))
    disc = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if disc and disc['flight_path_coords'] and disc['flight_data_image']:
        flight_path_coords = json.loads(disc['flight_path_coords'])
        flight_data_image = np.array(Image.open(io.BytesIO(disc['flight_data_image'])))
        return flight_path_coords, flight_data_image
    else:
        print("No flight path or image found for this disc.")
        return None, None

# Plot flight path on top of the flight data image
def plot_flight_path(disc_id):
    coordinates, flight_data_image = fetch_flight_path_data(disc_id)

    if coordinates and flight_data_image is not None:
        # Extract x and y coordinates
        x_coords = [point[0] for point in coordinates]
        y_coords = [point[1] for point in coordinates]

        # Plot the flight path on top of the image
        plt.figure(figsize=(5, 10))

        # Display the flight data image as background
        plt.imshow(cv2.cvtColor(flight_data_image, cv2.COLOR_RGB2RGBA))

        # Plot the coordinates
        plt.plot(x_coords, y_coords, marker='o', color='red', linewidth=2)

        # Set the grid's horizontal and vertical axis labels
        plt.xticks([0, 50, 100, 150], [-100, -50, 0, 50])
        plt.yticks([0, 17, 33, 50, 67, 84, 100, 117, 134, 150, 167])

        plt.xlabel('Horizontal Distance (%)')
        plt.ylabel('Vertical Distance (meters)')

        # Add grid lines
        plt.grid(True)

        plt.show()
    else:
        print("No coordinates or image found to plot.")

# Example usage 24 = green
if __name__ == "__main__":
    disc_id = 30  # Replace with the actual disc ID
    plot_flight_path(disc_id)
