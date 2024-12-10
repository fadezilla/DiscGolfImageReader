import mysql.connector
import json
import matplotlib.pyplot as plt

# Database settings
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Code9856",
    database="discgolf"
)
cursor = db.cursor()

# Replace with the desired disc ID
disc_id = 140 # Modify this as needed

# Fetch coordinates from the database for the given disc ID
query = "SELECT disc_flight_coords_extra, backhand_anhyzer FROM discs WHERE id = %s"
cursor.execute(query, (disc_id,))
result = cursor.fetchone()

if result:
    drawn_path = json.loads(result[0])  # disc_flight_coords_extra
    best_match_path = json.loads(result[1])  # backhand_hyzer

    # Extract x and y values for both paths
    drawn_x = [point["x"] for point in drawn_path]
    drawn_y = [point["y"] for point in drawn_path]
    best_x = [point["x"] for point in best_match_path]
    best_y = [point["y"] for point in best_match_path]

    # Plotting
    plt.figure(figsize=(10, 6))
    plt.plot(drawn_x, drawn_y, label="Drawn Path", color="red", marker="o", markersize=2)
    plt.plot(best_x, best_y, label="Best Match Path", color="blue", marker="x", markersize=2)

    # Adding grid lines to represent 5x10 blocks of 50x50 feet each
    plt.xticks(range(-100, 250, 50))  # X grid intervals
    plt.yticks(range(0, 500, 50))  # Y grid intervals
    plt.grid(True, which='both', color='gray', linestyle='--', linewidth=0.5)

    # Adding labels and legend
    plt.xlabel("X Coordinates (50 feet per grid)")
    plt.ylabel("Y Coordinates (50 feet per grid)")
    plt.title("Comparison of Drawn Path and Best Match Path")
    plt.legend()
    plt.show()

else:
    print(f"No data found for disc ID {disc_id}")

# Close the database connection
cursor.close()
db.close()
