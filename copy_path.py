import mysql.connector
import json
import cv2
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import io
import time

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
        print(f"No flight path or image found for disc ID {disc_id}.")
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

        plt.show()  # Display without blocking further execution
        time.sleep(1)  # Display each image for 5 seconds
        plt.close()  # Close the plot after displaying for 5 seconds

    else:
        print(f"No coordinates or image found to plot for disc ID {disc_id}.")

# Loop through all disc IDs and display flight paths
def display_all_flight_paths(start_id, end_id):
    for disc_id in range(start_id, end_id + 1):
        plot_flight_path(disc_id)

if __name__ == "__main__":
    start_id = 1  # Start with disc ID 1
    end_id = 7  # Set the range as needed (e.g., up to disc ID 50)
    display_all_flight_paths(start_id, end_id)
