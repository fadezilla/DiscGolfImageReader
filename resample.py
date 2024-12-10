import json
import os
import mysql.connector
import numpy as np
from scipy.interpolate import interp1d

# Connect to the database
db = mysql.connector.connect(
    host="localhost",  # Update with your DB settings
    user="root",        # Update with your DB user
    password="Code9856", # Update with your DB password
    database="discgolf"  # Update with your DB name
)
cursor = db.cursor()

# Resample path to have a fixed number of points using interpolation
def resample_path(path, num_points=100):
    if len(path) < 2:
        return path
    
    # Remove duplicate points
    unique_path = [path[0]]
    for point in path[1:]:
        if point != unique_path[-1]:
            unique_path.append(point)

    # Ensure continuous motion by filtering points that move backward
    filtered_path = [unique_path[0]]
    for point in unique_path[1:]:
        if point['y'] >= filtered_path[-1]['y']:  # Ensure y-coordinate is always increasing
            filtered_path.append(point)

    if len(filtered_path) < 2:
        return filtered_path
    
    # Extract x and y coordinates
    x_coords = [point['x'] for point in filtered_path]
    y_coords = [point['y'] for point in filtered_path]
    
    # Create interpolation functions
    original_indices = np.linspace(0, 1, num=len(filtered_path))
    target_indices = np.linspace(0, 1, num=num_points)
    
    interp_x = interp1d(original_indices, x_coords, kind='linear')
    interp_y = interp1d(original_indices, y_coords, kind='linear')
    
    # Generate resampled path
    resampled_path = [{"x": float(interp_x(t)), "y": float(interp_y(t))} for t in target_indices]
    return resampled_path

# Fetch all flight paths from the database
cursor.execute("SELECT id, disc_flight_coords FROM discs WHERE disc_flight_coords IS NOT NULL")
results = cursor.fetchall()

for disc_id, flight_coords in results:
    try:
        # Parse the JSON coordinates
        path = json.loads(flight_coords)
        
        # Resample to 100 points
        resampled_path = resample_path(path, num_points=100)
        
        # Convert back to JSON
        resampled_path_json = json.dumps(resampled_path)
        
        # Update the database with the resampled path in a new column
        cursor.execute(
            "UPDATE discs SET flight_coords_resampled = %s WHERE id = %s",
            (resampled_path_json, disc_id)
        )
        print(f"Updated disc ID {disc_id} with resampled path in flight_coords_resampled.")
    except json.JSONDecodeError:
        print(f"Failed to parse JSON for disc ID {disc_id}.")
    except Exception as e:
        print(f"Error processing disc ID {disc_id}: {e}")

# Commit changes and close the connection
db.commit()
cursor.close()
db.close()
