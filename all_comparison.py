import json
import mysql.connector
import matplotlib.pyplot as plt

# Connect to the database
db = mysql.connector.connect(
    host="localhost",  # Update with your DB settings
    user="root",        # Update with your DB user
    password="Code9856", # Update with your DB password
    database="discgolf"  # Update with your DB name
)
cursor = db.cursor()

# Function to fetch flight paths for a specific disc ID
def fetch_flight_paths(disc_id):
    cursor.execute("""
        SELECT flight_coords_resampled, backhand_hyzer, backhand_anhyzer, 
               forehand_hyzer, forehand_anhyzer, flat_forehand
        FROM discs WHERE id = %s
    """, (disc_id,))
    result = cursor.fetchone()
    
    if result is None:
        raise ValueError(f"No disc found with ID {disc_id}")

    return {
        "flight_coords_resampled": json.loads(result[0]),
        "backhand_hyzer": json.loads(result[1]),
        "backhand_anhyzer": json.loads(result[2]),
        "forehand_hyzer": json.loads(result[3]),
        "forehand_anhyzer": json.loads(result[4]),
        "flat_forehand": json.loads(result[5]),
    }

# Function to plot flight paths
def plot_flight_paths(flight_paths):
    colors = {
        "flight_coords_resampled": "blue",
        "backhand_hyzer": "red",
        "backhand_anhyzer": "green",
        "forehand_hyzer": "purple",
        "forehand_anhyzer": "orange",
        "flat_forehand": "black",
    }

    plt.figure(figsize=(10, 6))
    
    for path_type, path_coords in flight_paths.items():
        x_coords = [point['x'] for point in path_coords]
        y_coords = [point['y'] for point in path_coords]
        plt.plot(x_coords, y_coords, label=path_type.replace("_", " ").title(), color=colors[path_type], marker="o", markersize=4)

    # Adding grid lines to represent 5x10 blocks of 50x50 feet each
    plt.xticks(range(-100, 250, 50))  # X grid intervals
    plt.yticks(range(0, 500, 50))  # Y grid intervals
    plt.grid(True, which='both', color='gray', linestyle='--', linewidth=0.5)

    plt.xlabel("X Coordinates (50 feet per grid)")
    plt.ylabel("Y Coordinates (50 feet per grid)")
    plt.title("Comparison of Different Flight Paths for Disc")
    plt.legend()
    plt.show()

if __name__ == "__main__":
    disc_id = int(input("Enter the disc ID to plot flight paths: "))
    
    try:
        flight_paths = fetch_flight_paths(disc_id)
        plot_flight_paths(flight_paths)
    except ValueError as e:
        print(e)
    except Exception as e:
        print(f"An error occurred: {e}")

# Close the database connection
cursor.close()
db.close()

