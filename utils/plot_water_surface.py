import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Read CSV
csv_file = "Path/to/your_file.csv"
df = pd.read_csv(csv_file)

#Option to save the plot as a PNG file. If True, the plot will be saved to the specified path.
save = False
save_path = "Path/to/your_file_plot.png"

# Create figure
fig = plt.figure(figsize=(12, 9))
ax = fig.add_subplot(111, projection="3d")

DECIMATION = 100

# Plot Z values separately for each classification
classifications = np.sort(df["Classification"].unique())

for class_val in classifications:
    class_data = df[df["Classification"] == class_val]

    # Keep every 10th point
    class_data = class_data.iloc[::DECIMATION]

    ax.scatter(
        class_data["X"],
        class_data["Y"],
        class_data["Z"],
        s=8,
        label=f"Class {class_val}"
    )

# Valid calculated water-surface heights
surface_data = df[
    df["Water Surface Height"] != -9999
]

# Keep every 10th surface point
surface_data = surface_data.iloc[::DECIMATION]

ax.scatter(
    surface_data["X"],
    surface_data["Y"],
    surface_data["Water Surface Height"],
    color="cyan",
    s=12,
    marker="o",
    label="Water Surface"
)

ax.set_xlabel("X (Easting)")
ax.set_ylabel("Y (Northing)")
ax.set_zlabel("Z (Elevation)")

ax.set_title("Point Elevations and Water Surface by Classification")

ax.legend()

plt.tight_layout()

if save:
    plt.savefig(save_path, dpi=300)

plt.show()