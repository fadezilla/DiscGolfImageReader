import cv2
import numpy as np
import mysql.connector
import requests
from io import BytesIO
from PIL import Image

# Connect to the database
def connect_db():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Code9856",
        database="discgolf"
    )
    return conn

# Fetch all discs from the database
def fetch_all_discs():
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT d.id, d.flight_path 
        FROM discs d
        LEFT JOIN disc_flight_data df ON d.id = df.disc_id
        WHERE df.flight_data_image IS NULL
    """)
    discs = cursor.fetchall()
    cursor.close()
    conn.close()
    return discs

# Determine whether the image uses meters or feet
def match_template(image, template_path):
    template = cv2.imread(template_path, 0)
    result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    return max_val, max_loc

def determine_measurement_units(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    roi = gray[0:50, 0:60]

    m_score, _ = match_template(roi, 'meters.png')
    ft_score, _ = match_template(roi, 'Feet.png')

    if m_score > ft_score and m_score > 0.5:
        print("Detected units: meters")
        return "meters"
    elif ft_score > m_score and ft_score > 0.5:
        print("Detected units: feet")
        return "feet"
    else:
        print("Could not determine measurement units from the image.")
        return None

def process_flight_path(image_url):
    response = requests.get(image_url)
    if response.status_code != 200:
        raise Exception(f"Failed to download image: {response.status_code}")

    # Open image with PIL and convert to RGB
    image = Image.open(BytesIO(response.content)).convert("RGB")
    image_np = np.array(image)

    # Convert to BGR for OpenCV processing
    image_bgr = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)

    units = determine_measurement_units(image_bgr)

    if units == "meters":
        x_start, y_start, x_end, y_end = 28, 16, 169, 321
    elif units == "feet":
        x_start, y_start, x_end, y_end = 28, 16, 169, 315
    else:
        raise ValueError("Could not determine measurement units from the image.")

    # Crop the image
    roi_cropped_bgr = image_bgr[y_start:y_end, x_start:x_end]

    # Convert back to RGB before saving
    roi_cropped_rgb = cv2.cvtColor(roi_cropped_bgr, cv2.COLOR_BGR2RGB)

    # Encode the image in RGB format
    _, encoded_image = cv2.imencode('.png', cv2.cvtColor(roi_cropped_rgb, cv2.COLOR_RGB2BGR))

    return encoded_image.tobytes()

# Save processed flight data image to the database
# Save processed flight data image to the database
def save_flight_data_image(disc_id, flight_data_image):
    conn = connect_db()
    cursor = conn.cursor()
    insert_query = """
    INSERT INTO disc_flight_data (id, disc_id, flight_data_image) 
    VALUES (%s, %s, %s) 
    ON DUPLICATE KEY UPDATE flight_data_image = VALUES(flight_data_image)
    """
    # Setting both `id` and `disc_id` to the same value
    cursor.execute(insert_query, (disc_id, disc_id, flight_data_image))
    conn.commit()
    cursor.close()
    conn.close()


# Process all discs in the database
def process_all_discs():
    discs = fetch_all_discs()
    for disc in discs:
        try:
            disc_id = disc['id']
            image_url = disc['flight_path']
            
            # Skip if no flight_path is provided
            if not image_url:
                print(f"Skipping disc ID: {disc_id}, no flight path")
                continue
            
            print(f"Processing disc ID: {disc_id}")
            
            # Process the flight path image
            flight_data_image = process_flight_path(image_url)
            
            # Save the flight data image to the database
            save_flight_data_image(disc_id, flight_data_image)
            print(f"Flight data for disc ID {disc_id} saved.")
        except Exception as e:
            print(f"Error processing disc ID {disc_id}: {e}")

if __name__ == "__main__":
    process_all_discs()
