import json
import os
import mysql.connector
import numpy as np

# Connect to the database
db = mysql.connector.connect(
    host="localhost",  # Update with your DB settings
    user="root",        # Update with your DB user
    password="Code9856", # Update with your DB password
    database="discgolf"  # Update with your DB name
)
cursor = db.cursor()

def adjust_path_with_disc_attributes(path, angle_type, stability, disc_id):
    adjusted_path = []

    previous_y = None  # Track previous y-coordinate to ensure no backtracking
    previous_x = None  # Track previous x-coordinate to ensure continuous motion

    for index, point in enumerate(path):
        x, y = point['x'], point['y']

        # Initialize new_x and new_y to default to avoid unassigned errors
        new_x, new_y = x, y

        # Determine the progress along the path (0 to 1 scale)
        progress = index / len(path)

        if angle_type == 'backhand_hyzer':
            if stability in ['Overstable', 'Very Overstable']:
                # Overstable discs maintain a stronger left turn
                left_factor = 1.2 if stability == 'Overstable' else 1.25
                distance_factor = 0.9
            elif stability in ['Neutral', 'Stable']:
                # Neutral or stable discs will turn left more gradually and keep turning left
                left_factor = 1.15
                distance_factor = 0.95
            elif stability in ['Understable', 'Very Understable']:
                if progress < 0.5:
                    # Understable discs early in flight - slight left turn
                    left_factor = 1.05
                    distance_factor = 1.05
                else:
                    # Later in flight - fade slightly to the right
                    left_factor = 1.1 if stability == 'Understable' else 1.15
                    distance_factor = 1.1
            else:
                # Default values in case of unexpected stability
                left_factor = 1.0
                distance_factor = 1.0

            # Interpolate between old x and new_x for smoother transitions
            if previous_x is not None:
                new_x = previous_x + (x * left_factor - previous_x) * 0.1
            else:
                new_x = x * left_factor

            new_y = y * distance_factor

        elif angle_type == 'backhand_anhyzer':
            if stability in ['Overstable', 'Very Overstable']:
                if progress < 0.5:
                    # Overstable discs will have an S-curve, turning right first then fading left
                    right_factor = 0.9
                    distance_factor = 1.1
                else:
                    right_factor = 1.1 if stability == 'Overstable' else 1.15
                    distance_factor = 0.9
            elif stability in ['Neutral', 'Stable']:
                if progress < 0.5:
                    right_factor = 0.95
                    distance_factor = 1.05
                else:
                    right_factor = 1.05
                    distance_factor = 0.95
            elif stability in ['Understable', 'Very Understable']:
                right_factor = 0.85 if stability == 'Understable' else 0.8
                distance_factor = 1.1
            else:
                right_factor = 1.0
                distance_factor = 1.0

            # Interpolate between old x and new_x for smoother transitions
            if previous_x is not None:
                new_x = previous_x + (x * right_factor - previous_x) * 0.1
            else:
                new_x = x * right_factor

            new_y = y * distance_factor

        else:
            # Default values in case of unexpected angle_type
            new_x = x
            new_y = y
            print(f"Unexpected angle_type for disc ID {disc_id}: {angle_type}")

        # Ensure no backtracking in y-direction
        if previous_y is not None and new_y < previous_y:
            new_y = previous_y
            new_x = previous_x  # Keep x the same if y is adjusted to avoid backtracking

        previous_y = new_y
        previous_x = new_x

        adjusted_path.append({"x": new_x, "y": new_y})

    return adjusted_path

# Fetch all flight paths from the database
cursor.execute("SELECT id, disc_flight_coords_extra, stability, backhand_hyzer, backhand_anhyzer FROM discs WHERE disc_flight_coords_extra IS NOT NULL")
results = cursor.fetchall()

for disc_id, flight_coords, stability, existing_hyzer, existing_anhyzer in results:
    try:
        # Parse the JSON coordinates
        path = json.loads(flight_coords)
        existing_hyzer_path = json.loads(existing_hyzer) if existing_hyzer else None
        existing_anhyzer_path = json.loads(existing_anhyzer) if existing_anhyzer else None

        # Calculate different variations of the flight paths
        backhand_hyzer_path = adjust_path_with_disc_attributes(path, 'backhand_hyzer', stability, disc_id)
        backhand_anhyzer_path = adjust_path_with_disc_attributes(path, 'backhand_anhyzer', stability, disc_id)

        # Convert back to JSON
        backhand_hyzer_json = json.dumps(backhand_hyzer_path)
        backhand_anhyzer_json = json.dumps(backhand_anhyzer_path)

        # Check if the new paths are different from the existing ones
        if existing_hyzer_path != backhand_hyzer_path or existing_anhyzer_path != backhand_anhyzer_path:
            # Update the database with the adjusted paths
            cursor.execute("""
                UPDATE discs
                SET backhand_hyzer = %s, backhand_anhyzer = %s
                WHERE id = %s
            """, (backhand_hyzer_json, backhand_anhyzer_json, disc_id))

            if cursor.rowcount == 0:
                print(f"No rows updated for disc ID {disc_id}, check if the record exists.")
            else:
                print(f"Updated disc ID {disc_id} with adjusted flight paths.")
        else:
            print(f"No changes required for disc ID {disc_id}. Flight paths are identical.")
    except json.JSONDecodeError:
        print(f"Failed to parse JSON for disc ID {disc_id}.")
    except Exception as e:
        print(f"Error processing disc ID {disc_id}: {e}")

# Commit changes and close the connection
try:
    db.commit()
    print("Database changes committed successfully.")
except Exception as e:
    print(f"Error committing changes: {e}")
finally:
    cursor.close()
    db.close()
    print("Database connection closed.")
