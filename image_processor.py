import cv2
import numpy as np
import mysql.connector
import json

# Connect to the database
def connect_db():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Code9856",
        database="discgolf"
    )
    return conn

# Fetch all discs' flight path images where coordinates are not yet processed
# Fetch all discs' flight path images where coordinates are not yet processed
def fetch_all_flight_data_images():
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, flight_data_image 
        FROM disc_flight_data 
        WHERE flight_path_coords IS NULL
    """)  # Only discs without coordinates
    discs = cursor.fetchall()
    cursor.close()
    conn.close()
    return discs

# Detect the dominant color of the line
def detect_line_color(image):
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Define color ranges for red, blue, green, and orange
    color_ranges = {
        "red": [
            (np.array([0, 100, 100]), np.array([10, 255, 255])),
            (np.array([160, 100, 100]), np.array([180, 255, 255]))
        ],
        "blue": [(np.array([85, 125, 25]), np.array([145, 280, 175]))],
        "green": [(np.array([35, 100, 150]), np.array([85, 255, 255]))],
        "orange": [(np.array([10, 75, 145]), np.array([35, 260, 260]))]
    }

    max_pixels = 0
    detected_color = None
    for color, ranges in color_ranges.items():
        mask = sum(cv2.inRange(hsv_image, lower, upper) for lower, upper in ranges)
        pixel_count = cv2.countNonZero(mask)

        if pixel_count > max_pixels:
            max_pixels = pixel_count
            detected_color = color

    return detected_color

# Process using contrast for red and blue lines
def process_flight_path_by_contrast(image_data):
    np_image = np.frombuffer(image_data, np.uint8)
    image = cv2.imdecode(np_image, cv2.IMREAD_COLOR)

    # Convert image to grayscale
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply a binary threshold to get a black and white image
    _, thresholded_image = cv2.threshold(gray_image, 150, 255, cv2.THRESH_BINARY_INV)

    # Use morphological operations to clean up the image
    kernel = np.ones((3, 3), np.uint8)
    thresholded_image = cv2.morphologyEx(thresholded_image, cv2.MORPH_CLOSE, kernel)

    # Find contours (flight path will likely be the largest contour)
    contours, _ = cv2.findContours(thresholded_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        print("No flight path found")
        return []

    # Assuming the largest contour is the flight path
    largest_contour = max(contours, key=cv2.contourArea)

    # Extract coordinates
    path_data = [point[0].tolist() for point in largest_contour]
    
    return path_data

# Process using HSV color ranges for green and orange
def process_flight_path_by_hsv(image):
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    lower_green = np.array([35, 100, 150])
    upper_green = np.array([85, 255, 255])
    lower_orange = np.array([10, 75, 145])
    upper_orange = np.array([35, 260, 260])

    mask_green = cv2.inRange(hsv_image, lower_green, upper_green)
    mask_orange = cv2.inRange(hsv_image, lower_orange, upper_orange)

    combined_mask = mask_green | mask_orange

    kernel = np.ones((3, 3), np.uint8)
    cleaned_image = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel)
    cv2.imwrite("debug_cleaned_hsv.png", cleaned_image)

    edges = cv2.Canny(cleaned_image, 50, 150)
    cv2.imwrite("debug_edges_hsv.png", edges)

    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        print("No flight path found via HSV.")
        return []

    largest_contour = max(contours, key=cv2.contourArea)
    path_data = [point[0].tolist() for point in largest_contour]
    
    return path_data

# Save the flight path coordinates in the database
def save_flight_path_coords(disc_id, flight_path_coords):
    conn = connect_db()
    cursor = conn.cursor()
    update_query = "UPDATE disc_flight_data SET flight_path_coords = %s WHERE id = %s"
    cursor.execute(update_query, (json.dumps(flight_path_coords), disc_id))
    conn.commit()
    cursor.close()
    conn.close()

# Process all discs in the database
def process_all_flight_paths():
    discs = fetch_all_flight_data_images()
    for disc in discs:
        try:
            disc_id = disc['id']
            image_data = disc['flight_data_image']
            image = cv2.imdecode(np.frombuffer(image_data, np.uint8), cv2.IMREAD_COLOR)
            print(f"Processing flight path for disc ID: {disc_id}")

            # Detect line color
            detected_color = detect_line_color(image)
            print(f"Detected line color: {detected_color}")

            # Choose processing method based on color
            if detected_color in ['red', 'blue']:
                flight_path_coords = process_flight_path_by_contrast(image_data)
            else:
                flight_path_coords = process_flight_path_by_hsv(image)

            if flight_path_coords:
                save_flight_path_coords(disc_id, flight_path_coords)
                print(f"Flight path coordinates for disc ID {disc_id} saved.")
            else:
                print(f"No flight path detected for disc ID {disc_id}")
        except Exception as e:
            print(f"Error processing disc ID {disc_id}: {e}")

if __name__ == "__main__":
    process_all_flight_paths()
