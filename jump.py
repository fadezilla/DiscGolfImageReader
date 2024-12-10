import json
import mysql.connector

# Connect to the database
db = mysql.connector.connect(
    host="localhost",  # Update with your DB settings
    user="root",        # Update with your DB user
    password="Code9856", # Update with your DB password
    database="discgolf"  # Update with your DB name
)
cursor = db.cursor()

# Fetch all flight paths from the database
cursor.execute("SELECT id, flight_coords_resampled FROM discs WHERE flight_coords_resampled IS NOT NULL")
results = cursor.fetchall()

# Iterate over each disc and adjust flight path to have exactly 500 points
for disc_id, flight_coords in results:
    try:
        # Parse the JSON coordinates
        path = json.loads(flight_coords)
        
        # Check for jumps greater than 5 in y-coordinates and add intermediate points
        new_path = []
        for i in range(len(path) - 1):
            current_point = path[i]
            next_point = path[i + 1]
            new_path.append(current_point)
            
            y_diff = abs(next_point['y'] - current_point['y'])
            if y_diff > 5:
                # Calculate number of intermediate points needed
                num_points = int(y_diff // 5) + 1
                
                # Calculate step size for x and y
                x_step = (next_point['x'] - current_point['x']) / (num_points + 1)
                y_step = (next_point['y'] - current_point['y']) / (num_points + 1)
                
                # Add intermediate points
                for j in range(1, num_points + 1):
                    new_point = {
                        'x': current_point['x'] + j * x_step,
                        'y': current_point['y'] + j * y_step
                    }
                    new_path.append(new_point)
        
        # Add the last point
        new_path.append(path[-1])

        # Ensure the path has exactly 500 points
        total_points = len(new_path)
        if total_points < 500:
            # Calculate how many points are needed
            points_needed = 500 - total_points
            
            # Calculate distribution of points across the path
            interpolated_path = []
            for i in range(len(new_path) - 1):
                interpolated_path.append(new_path[i])
                segment_length = ((new_path[i + 1]['x'] - new_path[i]['x']) ** 2 + (new_path[i + 1]['y'] - new_path[i]['y']) ** 2) ** 0.5
                num_interpolations = max(1, int(points_needed * (segment_length / sum(
                    ((new_path[j + 1]['x'] - new_path[j]['x']) ** 2 + (new_path[j + 1]['y'] - new_path[j]['y']) ** 2) ** 0.5 for j in range(len(new_path) - 1)))))
                
                for j in range(1, num_interpolations + 1):
                    mid_point = {
                        'x': new_path[i]['x'] + j * (new_path[i + 1]['x'] - new_path[i]['x']) / (num_interpolations + 1),
                        'y': new_path[i]['y'] + j * (new_path[i + 1]['y'] - new_path[i]['y']) / (num_interpolations + 1)
                    }
                    interpolated_path.append(mid_point)
            interpolated_path.append(new_path[-1])
            new_path = interpolated_path[:500]
        elif total_points > 500:
            # If more than 500, downsample to 500 points
            step = len(new_path) / 500
            new_path = [new_path[int(i * step)] for i in range(500)]

        # Convert back to JSON
        new_flight_coords = json.dumps(new_path)

        # Update the database with the adjusted path
        cursor.execute("""
            UPDATE discs
            SET disc_flight_coords_extra = %s
            WHERE id = %s
        """, (new_flight_coords, disc_id))

        if cursor.rowcount == 0:
            print(f"No rows updated for disc ID {disc_id}, check if the record exists.")
        else:
            print(f"Updated disc ID {disc_id} with smoothed flight path.")

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
