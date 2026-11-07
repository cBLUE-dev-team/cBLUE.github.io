import laspy
import numpy as np
import logging

logger = logging.getLogger(__name__)

class SurfaceHeight:

    NO_DATA_VALUE = -9999.0

    def __init__(self, settings_object, las_files, sbet):
        self.bin_size = settings_object.water_bin_length
        
        self.subaqueous_classes = settings_object.subaqueous_classes
        self.sea_surface_classes = settings_object.sea_surface_classes
        self.ground_classes = settings_object.ground_classes

        if self.bin_size <= 0:
            raise ValueError("Water bin length must be greater than zero.")

        # Calculate the min and max values for x (easting, sbet.data.X) 
        # and y (northing, sbet.data.Y) coordinates to determine the range of the data.
        self.min_x = sbet.data.X.min()
        self.max_x = sbet.data.X.max()
        self.min_y = sbet.data.Y.min()
        self.max_y = sbet.data.Y.max()

        # Calculate the number of bins in each dimension, there will be a minimum of 1 bin in each dimension, even if the range is smaller than the bin size.
        self.num_bins_x = max(1, int(np.ceil((self.max_x - self.min_x) / self.bin_size)))
        self.num_bins_y = max(1, int(np.ceil((self.max_y - self.min_y) / self.bin_size)))

        # Calculate the average water-surface height for each bin using the provided LAS files.
        print("Calculating water surface heights for each bin...")
        self.height_array = self.get_height(las_files)

        # Calculate the flying height for the center of the dataset based on the SBET data.
        self.flying_height = self.get_flying_height(las_files, sbet) #las files, z values from SBET data
        

    def get_bin_indices(self, x, y):
        """
        Converts easting and northing coordinates into bin indices.

        Input:
        x = easting
        y = northing

        Returns:
        bin_x, bin_y

        Array access:
        height_array[bin_x, bin_y]

        """
        bin_x = int(np.floor((x - self.min_x) / self.bin_size))
        bin_y = int(np.floor((y - self.min_y) / self.bin_size))

        # If a coordinate lies exactly on the maximum boundary 
        # (self.max_x or self.max_y), the calculation above produces num_bins. 
        # Assign that point to the final valid bin instead (num_bins - 1).
        bin_x = np.clip(bin_x, 0, self.num_bins_x - 1)
        bin_y = np.clip(bin_y, 0, self.num_bins_y - 1)

        return bin_x, bin_y


    def get_height(self, las_files):
        """
        Calculate the average water-surface height for each bin. 
        Valid water-surface points are classified as either 41 or 42 listed in the cblue_configuration.json.
        Users can also define additional water-surface classes in the cblue_configuration.json file.

        Classification 41:
            Sea-surface point

        Classification 42:
            Synthetic water-surface point

        Input:
        las_files = List of LAS files containing point cloud data

        Returns:
        height_array = A 2D array of average water-surface heights for each bin. 
        If no valid water-surface points fall into a bin, the average height for 
        that bin is set to -9999 (default error value).
        """
        counts = np.zeros(
            (self.num_bins_x, self.num_bins_y),
            dtype=np.int32
        )

        sums = np.zeros(
            (self.num_bins_x, self.num_bins_y),
            dtype=np.float64
        )

        #Calculate the average surface height for each bin
        # Loop through each LAS file and extract the x, y, z, and classification data.
        for las_file in las_files:
            inFile = laspy.read(las_file)

            # Get a boolean mask for points classified as valid water-surface points 
            # (Default: sea-surface (41) or synthetic water-surface (42)).
            mask = np.isin(inFile.classification, self.sea_surface_classes)

            # Mask the x, y, z values to only include valid water-surface points.
            x = np.asarray(inFile.x[mask])
            y = np.asarray(inFile.y[mask])
            z = np.asarray(inFile.z[mask])

            # If there are no valid water-surface points in the LAS file, skip to the next file.
            if len(z) == 0:
                continue

            # Calculate the bin indices for each point and accumulate the number of points and sum of heights for each bin.
            bin_x = np.floor((x - self.min_x) / self.bin_size).astype(np.int32)
            bin_y = np.floor((y - self.min_y) / self.bin_size).astype(np.int32)

            # Clip the bin indices to ensure they are within the valid range of bins.
            bin_x = np.clip(bin_x, 0, self.num_bins_x - 1)
            bin_y = np.clip(bin_y, 0, self.num_bins_y - 1)

            # Use np.add.at to accumulate counts and sums for each bin. This handles duplicate indices correctly.
            np.add.at(counts, (bin_x, bin_y), 1)
            np.add.at(sums, (bin_x, bin_y), z)

        height_array = np.full(
            (self.num_bins_x, self.num_bins_y),
            self.NO_DATA_VALUE,
            dtype=np.float64
        )

        # Create a mask for bins that have at least one valid water-surface point.
        valid = counts > 0
        #  Calculate the average water surface height for those bins.
        height_array[valid] = sums[valid] / counts[valid]

        return height_array

    def get_nearest_surface_height(self, x, y, class_val):
        """
        Find the nearest valid water-surface bin to (x, y).

        Searches outward from the point up to max_distance.
        Returns NO_DATA_VALUE if no valid surface bin is found.
        """

        bin_x, bin_y = self.get_bin_indices(x, y)

        # If the point's own bin has a valid surface, use it immediately.
        if (0 <= bin_x < self.num_bins_x and 0 <= bin_y < self.num_bins_y):

            surface_height = self.height_array[bin_x, bin_y]

            if surface_height != self.NO_DATA_VALUE:
                return surface_height

        # If the point's own bin does not have a valid surface and 
        # the point is not classified as subaqueous, return NO_DATA_VALUE immediately.
        if class_val not in self.subaqueous_classes:
            return self.NO_DATA_VALUE

        # If this is a subaqueous point, extend the search outward from the point
        # to the nearest valid surface height, up to max_distance.
        nearest_height = self.NO_DATA_VALUE
        nearest_distance = np.inf
        max_distance = 20.0  # Maximum distance to search for a valid surface height (in meters)

        # Calculate the maximum number of bins to search based on max_distance, add 1 to ensure we cover near edges of bins that are partially within max_distance.
        max_bin_radius = int(np.ceil(max_distance / self.bin_size)) + 1

        # Search neighboring bins
        for neighbor_x in range(bin_x - max_bin_radius, bin_x + max_bin_radius + 1):
            for neighbor_y in range(bin_y - max_bin_radius, bin_y + max_bin_radius + 1):

                # Skip bins outside the array
                if not (0 <= neighbor_x < self.num_bins_x and
                        0 <= neighbor_y < self.num_bins_y):
                    continue

                surface_height = self.height_array[neighbor_x, neighbor_y]

                # Skip bins without surface data
                if surface_height == self.NO_DATA_VALUE:
                    continue

                # Find the distance from the point (x, y) to the edges of the neighboring bin
                bin_min_x = self.min_x + neighbor_x * self.bin_size
                bin_max_x = bin_min_x + self.bin_size
                bin_min_y = self.min_y + neighbor_y * self.bin_size
                bin_max_y = bin_min_y + self.bin_size

                dx = max(bin_min_x - x, 0, x - bin_max_x)
                dy = max(bin_min_y - y, 0, y - bin_max_y)
                distance = np.hypot(dx, dy)

                if distance <= max_distance and distance < nearest_distance:
                    nearest_distance = distance
                    nearest_height = surface_height


        return nearest_height

    def calculate_depth(self, x_data, y_data, z_data, classification):

        depth_data = np.full(len(x_data), self.NO_DATA_VALUE)  # Initialize depth_data with default error value
        surface_height_data = np.full(len(x_data), self.NO_DATA_VALUE)  # Initialize surface_height_data with default error value

        # Loop through each point and calculate the depth based on the nearest surface height.
        for i, (x, y, z, class_val) in enumerate(zip(x_data, y_data, z_data, classification)):
            # Get the nearest surface height for the current point (x, y).
            surface_height_data[i] = self.get_nearest_surface_height(x, y, class_val)

            # If a valid surface height was found, calculate the depth as the difference between the surface height and the point's z value.
            if surface_height_data[i] != self.NO_DATA_VALUE:
                depth_data[i] = surface_height_data[i] - z
                # print(f"Depth at ({x}, {y}, {z}): {depth}")

                
        return depth_data, surface_height_data

    def get_flying_height(self, las_files, sbet):
        """
        Calculate the flying height for the center of the dataset based on the SBET data. 
        Returns NO_DATA_VALUE if no valid ground or water-surface point is found in the SBET data.

        Input:
        z_las = A 1D array of z values from the LAS data.
        z_sbet = A 1D array of z values from the SBET data.

        Returns:
        flying_height = The flying height in meters for the center of the dataset based on the z values in the SBET data. 
                        Returns NO_DATA_VALUE if no valid ground or water-surface point is found in the SBET data.
        """

        las_z_point = self.NO_DATA_VALUE  # Initialize las_z_point with default error value
        sbet_z_point = self.NO_DATA_VALUE  # Initialize sbet_z_point with default error value
        valid_classes = set(self.sea_surface_classes + self.ground_classes)

        #Loop through each LAS file until a valid water-surface or ground point is found
        for las_file in las_files:

            if las_z_point != self.NO_DATA_VALUE:
                break  # Exit the loop if a valid surface height is found

            inFile = laspy.read(las_file)

            # Get the midpoint of the flight to start the search for a valid water-surface height.
            # // is flooring division, which returns the largest integer less than or equal to the division result.
            len_las = len(inFile.z)
            mid_index = len_las // 2

            # Get the indices of valid water-surface or ground points in the LAS data based on the classification values.
            valid_mask = np.isin(inFile.classification, list(valid_classes))

            valid_indices = np.flatnonzero(valid_mask)

            if valid_indices.size > 0:
                # Find the index of the valid point closest to the midpoint of the flight.
                closest_idx = valid_indices[np.argmin(np.abs(valid_indices - mid_index))].item()  # Convert to a standard Python integer

                las_z_point = inFile.z[closest_idx]
                las_timestamp = inFile.gps_time[closest_idx]


        # If a valid surface height was found in the LAS data, find the corresponding z value in the SBET data.
        if las_z_point != self.NO_DATA_VALUE:
            start_time = las_timestamp
            end_time = las_timestamp
            sbet_data = sbet.get_tile_data_by_time(start_time, end_time)

            if not sbet_data.empty:

                nearest_idx = np.abs(sbet_data["time"].values - las_timestamp).argmin()
                sbet_z_point = sbet_data.iloc[nearest_idx]["Z"]


        if sbet_z_point == self.NO_DATA_VALUE or las_z_point == self.NO_DATA_VALUE:
            return self.NO_DATA_VALUE

        # print(f"SBET z value: {sbet_z_point}, LAS z value: {las_z_point}")
        # print(f"Flying height: {sbet_z_point - las_z_point}")
        # Calculate the flying height for the center of the dataset
        return sbet_z_point - las_z_point