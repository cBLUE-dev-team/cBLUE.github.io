import numpy as np

class SurfaceHeight:

    NO_DATA_VALUE = -9999.0

    def __init__(self, water_bin_length, merged_data, classification):
        self.bin_size = water_bin_length

        if self.bin_size <= 0:
            raise ValueError("Water bin length must be greater than zero.")

        # Calculate the min and max values for x (easting, merged_data[2]) 
        # and y (northing, merged_data[3]) coordinates to determine the range of the data.
        self.min_x = merged_data[2].min()
        self.max_x = merged_data[2].max()
        self.min_y = merged_data[3].min()
        self.max_y = merged_data[3].max()

        # Calculate the number of bins in each dimension, there will be a minimum of 1 bin in each dimension, even if the range is smaller than the bin size.
        self.num_bins_x = max(1, int(np.ceil((self.max_x - self.min_x) / self.bin_size)))
        self.num_bins_y = max(1, int(np.ceil((self.max_y - self.min_y) / self.bin_size)))

        self.height_array = self.get_height(
            merged_data[2], # x (easting) points
            merged_data[3], # y (northing) points
            merged_data[4], # z (height)points
            classification  # point classification
        )

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
        if x == self.max_x:
            bin_x = self.num_bins_x - 1

        if y == self.max_y:
            bin_y = self.num_bins_y - 1

        return bin_x, bin_y   


    def get_height(self, x_points, y_points, z_points, classification):
        """
        Calculate the average water-surface height for each bin. 
        Valid water-surface points are classified as either 41 or 42.

        Classification 41:
            Sea-surface point

        Classification 42:
            Synthetic water-surface point

        Input:
        x_points = easting points (merged_data[2])
        y_points = northing points (merged_data[3])
        z_points = height points (merged_data[4])
        classification = point classification

        Returns:
        height_array = A 2D array of average water-surface heights for each bin. 
        If no valid water-surface points fall into a bin, the average height for 
        that bin is set to -9999 (default error value).
        """
        # Custom structure for each bin
        bin_dtype = np.dtype([
            ('num_points', int), #Number of points in the bin
            ('sum_height_points', float), #Sum of heights for all points in the bin
            ('avg_height', float) #Average height for the bin (sum_height_points/num_points)
        ])

        # Create a 2D array to store the surface heights
        height_array = np.zeros(
                            (self.num_bins_x, self.num_bins_y),
                            dtype=bin_dtype
        )
        # Fill the array with default error values
        height_array['avg_height'] = self.NO_DATA_VALUE

        #Calculate the average surface height for each bin
        for x, y, z, class_point in zip(x_points, y_points, z_points, classification):
            # Check if the point is class 41 (sea surface) or 42 (synthetic water surface)
            if class_point in (41, 42):
                # Calculate the bin indices for the point
                bin_x, bin_y = self.get_bin_indices(x, y)

                # Update the values for the bin
                height_array[bin_x, bin_y]['num_points'] += 1
                height_array[bin_x, bin_y]['sum_height_points'] += z

        # Get the list of populated bins (bins with at least one valid water-surface point)
        populated_bins = height_array['num_points'] > 0
        # Calculate the average height for each populated bin
        np.divide(
            height_array['sum_height_points'],
            height_array['num_points'],
            out=height_array['avg_height'],
            where=populated_bins
        )

        return height_array['avg_height'].copy()

    def calculate_depth(self, x_data, y_data, z_data):

        depth_data = np.full(len(x_data), self.NO_DATA_VALUE)  # Initialize depth_data with default error value

        for i, (x, y, z) in enumerate(zip(x_data, y_data, z_data)):
            # Calculate the bin indices for the point
            bin_x, bin_y = self.get_bin_indices(x, y)

            # Check if the bin indices are within the bounds of the height array, make sure we are not calculating depth without sea surface data.
            if 0 <= bin_x < self.num_bins_x and 0 <= bin_y < self.num_bins_y:
                avg_height = self.height_array[bin_x, bin_y]
                if avg_height != self.NO_DATA_VALUE:
                    depth_data[i] = avg_height - z
                    # print(f"Depth at ({x}, {y}, {z}): {depth}")
            else:               
                print(f"Point ({x}, {y}) is out of bounds for the height array.")
                
        return depth_data