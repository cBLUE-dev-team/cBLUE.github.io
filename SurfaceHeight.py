import numpy as np

class SurfaceHeight:


    def __init__(self, las_data):
        self.bin_size = 10 #meters

        # Custom structure for each bin
        self.bin_dtype = np.dtype([
        ('num_points', int), #Number of points in the bin
        ('sum_height_points', float), #Sum of heights for all points in the bin
        ('avg_height', float) #Average height for the bin (num_points/sum_height_points)
        ])

        self.height_array = self.get_height(las_data)



    def get_height(self, las_data):
        
        min_x = las_data.x.min()
        max_x = las_data.x.max()
        min_y = las_data.y.min()
        max_y = las_data.y.max()

        # Calculate the number of bins in each dimension
        num_bins_x = int((max_x - min_x) / self.bin_size)
        num_bins_y = int((max_y - min_y) / self.bin_size)
        # Create a 2D array to store the surface heights
        self.height_array = np.zeros(
                            (num_bins_y, num_bins_x),
                            dtype=self.bin_dtype
        )
        # Fill the array with default error values
        self.height_array['avg_height'] = -9999


        #Calculate the average surface height for each bin
        for point in las_data:
            # Check if the point is class 41 (sea surface) or 42 (synthetic water surface)
            if point.classification in [41, 42]:
                # Calculate the bin indices for the point
                bin_x = int((point.x - min_x) / self.bin_size)
                bin_y = int((point.y - min_y) / self.bin_size)

                # Update the values for the bin
                self.height_array[bin_y, bin_x]['num_points'] += 1
                self.height_array[bin_y, bin_x]['sum_height_points'] += point.z

        for y in range(num_bins_y):
            for x in range(num_bins_x):
                if self.height_array[y, x]['num_points'] > 0:
                    self.height_array[y, x]['avg_height'] = self.height_array[y, x]['sum_height_points'] / self.height_array[y, x]['num_points']
                # If no points fall into the bin, set the average height to a default errorvalue
                else:
                    self.height_array[y, x]['avg_height'] = -9999

        return self.height_array['avg_height']

    def calculate_depth(self, x_data, y_data, z_data):

        depth_data = np.full(len(x_data), -9999)  # Initialize depth_data with default error value

        for i, x, y, z in enumerate(zip(x_data, y_data, z_data)):
            # Calculate the bin indices for the point
            bin_x = int((x - self.height_array['avg_height'].min()) / self.bin_size)
            bin_y = int((y - self.height_array['avg_height'].min()) / self.bin_size)

            # Check if the bin indices are within the bounds of the height array
            if 0 <= bin_x < self.height_array.shape[1] and 0 <= bin_y < self.height_array.shape[0]:
                avg_height = self.height_array[bin_y, bin_x]['avg_height']
                if avg_height != -9999:
                    depth_data[i] = avg_height - z
                    # print(f"Depth at ({x}, {y}, {z}): {depth}")
            else:               
                print(f"Point ({x}, {y}) is out of bounds for the height array.")
                
        return depth_data