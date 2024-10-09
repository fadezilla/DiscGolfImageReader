from database import fetch_single_disc_image
from image_processor import extract_flight_path
import json

def main():
    # Fetch the image URL from the database
    disc = fetch_single_disc_image()
    image_url = disc['flight_path']

    # Process the image to extract flight path data
    flight_path_data = extract_flight_path(image_url)

    # Save the extracted path data to a JSON file
    with open('flight_path.json', 'w') as f:
        json.dump({"flight_path": flight_path_data}, f)

    print("Flight path data saved to flight_path.json")

if __name__ == "__main__":
    main()