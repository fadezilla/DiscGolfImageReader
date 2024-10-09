import cv2
import requests
from io import BytesIO
from PIL import Image
import numpy as np

def manual_select_roi(image_url, x_start, y_start, x_end, y_end):
    # Download the image using requests
    response = requests.get(image_url)
    if response.status_code != 200:
        raise Exception(f"Failed to download image: {response.status_code}")

    # Convert the image content to a format OpenCV can handle
    image = Image.open(BytesIO(response.content)).convert("RGB")
    image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

    # Manually specify the ROI coordinates
    roi_cropped = image[y_start:y_end, x_start:x_end]

    # Save the selected ROI as a PNG
    roi_filename = "selected_roi.png"
    cv2.imwrite(roi_filename, roi_cropped)
    print(f"Selected ROI saved as '{roi_filename}' with corners: {(x_start, y_start, x_end, y_end)}")

    # Display the saved ROI image
    roi_image = cv2.imread(roi_filename)
    cv2.imshow("Selected ROI", roi_image)
    cv2.waitKey(0)  # Wait for a key press to close the window

    # Close all windows
    cv2.destroyAllWindows()

if __name__ == "__main__":
    # Replace this URL with the image URL you want to work with
    image_url = "https://s3.amazonaws.com/media.marshallstreetdiscgolf.com/inbounds/8080444.webp"

    # Manually set the ROI coordinates (x_start, y_start, x_end, y_end)
    x_start = 0  # Example values, adjust these
    y_start = 0   # Example values, adjust these
    x_end = 24    # Example values, adjust these
    y_end = 25    # Example values, adjust these

    # Call the function to manually select and save ROI
    manual_select_roi(image_url, x_start, y_start, x_end, y_end)
