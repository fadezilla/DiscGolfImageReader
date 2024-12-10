import cv2
import numpy as np
import mysql.connector
import json
from scipy.interpolate import interp1d

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
def fetch_all_flight_data_images():
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, flight_data_image 
        FROM disc_flight_data 
    """)
    discs = cursor.fetchall()
    cursor.close()
    conn.close()
    return discs

# Normalize and interpolate coordinates
def normalize_and_interpolate(coords, num_points=50, grid_width=250, grid_height=500):
    x_values = [point[0] for point in coords]
    y_values = [point[1] for point in coords]

    # Normalize the coordinates
    min_x, max_x = min(x_values), max(x_values)
    min_y, max_y = min(y_values), max(y_values)
    
    normalized_coords = []
    for x, y in coords:
        norm_x = ((x - min_x) / (max_x - min_x)) * grid_width
        norm_y = ((y - min_y) / (max_y - min_y)) * grid_height
        normalized_coords.append([norm_x, norm_y])

    # Interpolate to ensure 50 coordinate points
    normalized_coords = np.array(normalized_coords)
    f_x = interp1d(np.linspace(0, 1, len(normalized_coords)), normalized_coords[:, 0], kind='linear')
    f_y = interp1d(np.linspace(0, 1, len(normalized_coords)), normalized_coords[:, 1], kind='linear')
    
    interpolated_coords = [[float(f_x(i/num_points)), float(f_y(i/num_points))] for i in range(num_points)]
    
    return interpolated_coords

# Extract centerline from two lines (if detected)
def extract_centerline(contour_coords):
    centerline = []
    for i in range(0, len(contour_coords) - 1, 2):
        left_point = contour_coords[i]
        right_point = contour_coords[i + 1]
        center_x = (left_point[0] + right_point[0]) / 2
        center_y = (left_point[1] + right_point[1]) / 2
        centerline.append([center_x, center_y])
    return centerline

# Detect the dominant color of the line
def detect_line_color(image):
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    color_ranges = {
        "red": [(np.array([0, 100, 100]), np.array([10, 255, 255])),
                (np.array([160, 100, 100]), np.array([180, 255, 255]))],
        "blue": [(np.array([85, 125, 25]), np.array([145, 280, 175]))],
        "green": [(np.array([35, 100, 150]), np.array([85, 255, 255]))],
        "orange": [(np.array([10, 75, 145]), np.array([35, 260, 260]))]
    }
    max_pixels, detected_color = 0, None
    for color, ranges in color_ranges.items():
        mask = sum(cv2.inRange(hsv_image, lower, upper) for lower, upper in ranges)
        pixel_count = cv2.countNonZero(mask)
        if pixel_count > max_pixels:
            max_pixels, detected_color = pixel_count, color
    return detected_color

# Process using contrast for red and blue lines
def process_flight_path_by_contrast(image_data):
    np_image = np.frombuffer(image_data, np.uint8)
    image = cv2.imdecode(np_image, cv2.IMREAD_COLOR)

    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresholded_image = cv2.threshold(gray_image, 150, 255, cv2.THRESH_BINARY_INV)

    kernel = np.ones((3, 3), np.uint8)
    thresholded_image = cv2.morphologyEx(thresholded_image, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(thresholded_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        print("No flight path found")
        return []

    largest_contour = max(contours, key=cv2.contourArea)
    path_data = [point[0].tolist() for point in largest_contour]

    # Extract centerline and interpolate
    centerline_coords = extract_centerline(path_data)
    return normalize_and_interpolate(centerline_coords)

# Process using HSV color ranges for green and orange
def process_flight_path_by_hsv(image):
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    lower_green, upper_green = np.array([35, 100, 150]), np.array([85, 255, 255])
    lower_orange, upper_orange = np.array([10, 75, 145]), np.array([35, 260, 260])

    mask_green = cv2.inRange(hsv_image, lower_green, upper_green)
    mask_orange = cv2.inRange(hsv_image, lower_orange, upper_orange)

    combined_mask = mask_green | mask_orange
    kernel = np.ones((3, 3), np.uint8)
    cleaned_image = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel)

    edges = cv2.Canny(cleaned_image, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        print("No flight path found via HSV.")
        return []

    largest_contour = max(contours, key=cv2.contourArea)
    path_data = [point[0].tolist() for point in largest_contour]

    # Extract centerline and interpolate
    centerline_coords = extract_centerline(path_data)
    return normalize_and_interpolate(centerline_coords)

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

            detected_color = detect_line_color(image)
            print(f"Detected line color: {detected_color}")

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