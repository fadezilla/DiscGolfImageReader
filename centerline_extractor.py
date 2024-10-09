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
        print(f"No flight path or image found for disc ID {disc_id}.")
        return None, None

# Extract the centerline from the flight path coordinates
def extract_centerline(contour_coords):
    centerline = []
    i = 0
    while i < len(contour_coords) - 1:
        x1, y1 = contour_coords[i]
        x2, y2 = contour_coords[i + 1]
        
        # Assuming side-by-side points have minimal y-difference and x-distance
        if abs(y2 - y1) < 5 and abs(x2 - x1) < 15:  # Adjust thresholds as necessary
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            centerline.append([center_x, center_y])
            i += 2  # Skip the next point since it's part of the pair
        else:
            centerline.append([x1, y1])  # Add single point if no pairing
            i += 1

    # Include last point if not added
    if i == len(contour_coords) - 1:
        centerline.append(contour_coords[-1])

    return centerline

# Plot flight path and centerline on top of the flight data image
def plot_flight_path_and_centerline(disc_id):
    coordinates, flight_data_image = fetch_flight_path_data(disc_id)

    if coordinates and flight_data_image is not None:
        # Extract x and y coordinates for the original path
        x_coords = [point[0] for point in coordinates]
        y_coords = [point[1] for point in coordinates]

        # Extract centerline
        centerline_coords = extract_centerline(coordinates)
        x_centerline = [point[0] for point in centerline_coords]
        y_centerline = [point[1] for point in centerline_coords]

        # Plot the flight path and centerline on top of the image
        plt.figure(figsize=(5, 10))

        # Display the flight data image as background
        plt.imshow(cv2.cvtColor(flight_data_image, cv2.COLOR_RGB2RGBA))

        # Plot the original flight path
        plt.plot(x_coords, y_coords, marker='o', color='red', linewidth=2, label='Original Path')

        # Plot the centerline
        plt.plot(x_centerline, y_centerline, marker='x', color='blue', linewidth=2, linestyle='--', label='Centerline')

        # Set the grid's horizontal and vertical axis labels
        plt.xticks([0, 50, 100, 150], [-100, -50, 0, 50])
        plt.yticks([0, 17, 33, 50, 67, 84, 100, 117, 134, 150, 167])

        plt.xlabel('Horizontal Distance (%)')
        plt.ylabel('Vertical Distance (meters)')

        # Add grid lines and legend
        plt.grid(True)
        plt.legend()

        plt.title(f'Disc ID {disc_id} - Flight Path and Centerline')
        plt.show()
    else:
        print(f"No coordinates or image found to plot for disc ID {disc_id}.")

if __name__ == "__main__":
    # Set a single disc ID to process
    disc_id = 1  # Adjust this ID to test specific discs
    plot_flight_path_and_centerline(disc_id)
