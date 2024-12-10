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

def adjust_path_with_disc_attributes(path, angle_type, speed, glide, turn, fade, stability):
    adjusted_path = []
    
    # Coefficients to adjust the influence based on disc properties
    speed_factor = speed / 15.0  # Normalize speed (since max speed is 15)
    glide_factor = glide / 7.0   # Assuming max glide is 7
    turn_factor = (turn + 5) / 7.0  # Normalizing turn to scale between -5 to +2
    fade_factor = fade / 6.0     # Normalizing fade to scale between 0 to 6

    # Hyzer Flip Up Effect: Apply flip-up logic for certain discs with hyzer
    flip_start_threshold = len(path) * 0.25  # When the disc starts flipping up (early in flight)
    flip_end_threshold = len(path) * 0.5     # When the disc reaches flat orientation

    fade_start_threshold = len(path) * 0.7  # When the disc starts fading back (late in flight)

    previous_x = None  # Track previous x-coordinate to ensure no backtracking

    for index, point in enumerate(path):
        x, y = point['x'], point['y']

        if angle_type == 'backhand_hyzer':
            # Backhand Hyzer - adjust based on stability
            if stability in ['overstable', 'very overstable']:
                # Overstable discs maintain the hyzer angle throughout the flight
                new_x = x * (1.0 - 0.3 * fade_factor)  # Consistent left fade
                new_y = y * (1.0 + 0.1 * glide_factor)
            else:
                # Understable or stable discs - start with hyzer and flip up
                if index <= flip_start_threshold:
                    # Initial hyzer angle (fade left more aggressively)
                    new_x = x * (1.0 - 0.3 * fade_factor)
                    new_y = y * (1.0 + 0.1 * glide_factor)
                elif flip_start_threshold < index <= flip_end_threshold:
                    # Gradually reduce hyzer angle to flat
                    progress = (index - flip_start_threshold) / (flip_end_threshold - flip_start_threshold)
                    new_x = x * (1.0 - 0.3 * fade_factor * (1.0 - progress))
                    new_y = y * (1.0 + 0.1 * glide_factor * (1.0 - progress))
                elif flip_end_threshold < index <= fade_start_threshold:
                    # Flat phase, similar to the original flight
                    new_x = x
                    new_y = y
                else:
                    # Fade back at the end of the flight
                    fade_progress = (index - fade_start_threshold) / (len(path) - fade_start_threshold)
                    new_x = x * (1.0 - 0.3 * fade_factor * fade_progress)
                    new_y = y * (1.0 + 0.1 * fade_factor * fade_progress)
                    new_x -= fade_factor * fade_progress  # Adding left fade movement to x-axis

        elif angle_type == 'backhand_anhyzer':
            # Backhand Anhyzer - starts with right turn, fades back
            if stability in ['understable', 'very understable']:
                new_x = x * (1.0 - 0.2 * turn_factor)  # Strong right turn throughout
                new_y = y * (1.0 + 0.1 * glide_factor) # Increase glide effect for more distance
            else:
                if index <= fade_start_threshold:
                    new_x = x * (1.0 - 0.2 * turn_factor)  # Strong right turn initially
                    new_y = y * (1.0 + 0.1 * glide_factor)
                else:
                    fade_progress = (index - fade_start_threshold) / (len(path) - fade_start_threshold)
                    new_x = x * (1.0 - 0.2 * turn_factor * (1.0 - fade_progress))  # Reduce right turn as it fades back
                    new_y = y * (1.0 + 0.1 * fade_factor * fade_progress)

        elif angle_type == 'forehand_hyzer':
            # Forehand Hyzer - starts with right fade, flips up if understable
            if stability in ['understable', 'neutral']:
                if index <= flip_start_threshold:
                    new_x = abs(x) * -1.0 * (1.0 - 0.15 * fade_factor)
                    new_y = y * (1.0 - 0.1 * turn_factor)
                elif flip_start_threshold < index <= flip_end_threshold:
                    progress = (index - flip_start_threshold) / (flip_end_threshold - flip_start_threshold)
                    new_x = abs(x) * -1.0 * (1.0 - 0.15 * fade_factor * (1.0 - progress))
                    new_y = y * (1.0 - 0.1 * turn_factor * (1.0 - progress))
                else:
                    new_x = abs(x) * -1.0
                    new_y = y
            else:
                new_x = abs(x) * -1.0 * (1.0 - 0.15 * fade_factor)
                new_y = y * (1.0 - 0.1 * turn_factor)

        elif angle_type == 'forehand_anhyzer':
            # Forehand Anhyzer - starts with left turn, fades back
            if stability in ['understable', 'very understable']:
                new_x = abs(x) * -1.0 * (1.0 + 0.2 * turn_factor)
                new_y = y * (1.0 + 0.1 * glide_factor)
            else:
                if index <= fade_start_threshold:
                    new_x = abs(x) * -1.0 * (1.0 + 0.2 * turn_factor)
                    new_y = y * (1.0 + 0.1 * glide_factor)
                else:
                    fade_progress = (index - fade_start_threshold) / (len(path) - fade_start_threshold)
                    new_x = abs(x) * -1.0 * (1.0 + 0.2 * turn_factor * (1.0 - fade_progress))
                    new_y = y * (1.0 + 0.1 * fade_factor * fade_progress)

        elif angle_type == 'flat_forehand':
            new_x = -x  # Invert x-axis to simulate forehand being opposite to backhand
            new_y = y

        else:
            # Default values in case of unexpected angle_type
            new_x = x
            new_y = y

        # Ensure no backtracking in x-direction
        if previous_x is not None:
            if angle_type.startswith("forehand"):
                if new_x > previous_x:
                    new_x = previous_x
            else:
                if new_x < previous_x:
                    new_x = previous_x

        previous_x = new_x

        adjusted_path.append({"x": new_x, "y": new_y})

    return adjusted_path



# Fetch all flight paths from the database
cursor.execute("SELECT id, flight_coords_resampled, speed, glide, turn, fade, stability FROM discs WHERE flight_coords_resampled IS NOT NULL")
results = cursor.fetchall()

for disc_id, flight_coords, speed, glide, turn, fade, stability in results:
    try:
        # Parse the JSON coordinates
        path = json.loads(flight_coords)

        # Calculate different variations of the flight paths
        backhand_hyzer_path = adjust_path_with_disc_attributes(path, 'backhand_hyzer', speed, glide, turn, fade, stability)
        backhand_anhyzer_path = adjust_path_with_disc_attributes(path, 'backhand_anhyzer', speed, glide, turn, fade, stability)
        forehand_hyzer_path = adjust_path_with_disc_attributes(path, 'forehand_hyzer', speed, glide, turn, fade, stability)
        forehand_anhyzer_path = adjust_path_with_disc_attributes(path, 'forehand_anhyzer', speed, glide, turn, fade, stability)
        flat_forehand_path = adjust_path_with_disc_attributes(path, 'flat_forehand', speed, glide, turn, fade, stability)

        # Convert back to JSON
        backhand_hyzer_json = json.dumps(backhand_hyzer_path)
        backhand_anhyzer_json = json.dumps(backhand_anhyzer_path)
        forehand_hyzer_json = json.dumps(forehand_hyzer_path)
        forehand_anhyzer_json = json.dumps(forehand_anhyzer_path)
        flat_forehand_json = json.dumps(flat_forehand_path)

        # Update the database with the adjusted paths
        cursor.execute("""
            UPDATE discs
            SET backhand_hyzer = %s,
                backhand_anhyzer = %s,
                forehand_hyzer = %s,
                forehand_anhyzer = %s,
                flat_forehand = %s
            WHERE id = %s
        """, (backhand_hyzer_json, backhand_anhyzer_json, forehand_hyzer_json, forehand_anhyzer_json, flat_forehand_json, disc_id))

        print(f"Updated disc ID {disc_id} with adjusted flight paths.")
    except json.JSONDecodeError:
        print(f"Failed to parse JSON for disc ID {disc_id}.")
    except Exception as e:
        print(f"Error processing disc ID {disc_id}: {e}")

# Commit changes and close the connection
db.commit()
cursor.close()
db.close()
