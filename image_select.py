import cv2
import numpy as np
import requests
from io import BytesIO
from PIL import Image

def match_template(image, template_path):
    template = cv2.imread(template_path, 0)
    result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    return max_val, max_loc

def determine_measurement_units(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    roi = gray[0:50, 0:60]

    m_score, _ = match_template(roi, 'meters.png')
    ft_score, _ = match_template(roi, 'feet.png')

    if m_score > ft_score and m_score > 0.5:
        print("Detected units: meters")
        return "meters"
    elif ft_score > m_score and ft_score > 0.5:
        print("Detected units: feet")
        return "feet"
    else:
        print("Could not determine measurement units from the image.")
        return None

def select_roi_based_on_units(image_url):
    response = requests.get(image_url)
    if response.status_code != 200:
        raise Exception(f"Failed to download image: {response.status_code}")

    image = Image.open(BytesIO(response.content)).convert("RGB")
    image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

    units = determine_measurement_units(image)

    if units == "meters":
        x_start, y_start, x_end, y_end = 28, 16, 169, 321
    elif units == "feet":
        x_start, y_start, x_end, y_end = 28, 16, 169, 315
    else:
        raise ValueError("Could not determine measurement units from the image.")

    roi_cropped = image[y_start:y_end, x_start:x_end]
    roi_filename = "selected_roi.png"
    cv2.imwrite(roi_filename, roi_cropped)
    print(f"Selected ROI saved as '{roi_filename}' for image with {units} units.")

if __name__ == "__main__":
    image_url = "https://s3.amazonaws.com/media.marshallstreetdiscgolf.com/inbounds/5634740.webp"
    select_roi_based_on_units(image_url)
