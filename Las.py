import numpy as np
import numexpr as ne
import laspy


class Las:

    def __init__(self, las):
        self.las = las
        self.las_short_name = las.split('\\')[-1]
        self.las_base_name = self.las_short_name.replace('.las', '')
        self.inFile = laspy.file.File(self.las, mode="r")
        self.num_file_points = self.inFile.__len__()
        print('{} has {} points.'.format(self.las_short_name, self.num_file_points))
        self.points_to_process = self.inFile.points['point']

    def get_flight_line_ids(self):
        return np.unique(self.points_to_process['pt_src_id'])

    def get_flight_line_txyz(self, fl):
        scale_x = np.asarray(self.inFile.header.scale[0])
        scale_y = np.asarray(self.inFile.header.scale[1])
        scale_z = np.asarray(self.inFile.header.scale[2])
        offset_x = np.asarray(self.inFile.header.offset[0])
        offset_y = np.asarray(self.inFile.header.offset[1])
        offset_z = np.asarray(self.inFile.header.offset[2])

        flight_line_indx = self.points_to_process['pt_src_id'] == fl
        flight_line_points = self.points_to_process[flight_line_indx]
        flight_line_points_sorted = np.sort(flight_line_points, order='gps_time')

        t = flight_line_points_sorted['gps_time']
        X = flight_line_points_sorted['X']
        Y = flight_line_points_sorted['Y']
        Z = flight_line_points_sorted['Z']

        x = ne.evaluate("X * scale_x + offset_x")
        y = ne.evaluate("Y * scale_y + offset_y")
        z = ne.evaluate("Z * scale_z + offset_z")

        return t, x, y, z

    def get_average_depth(self):  # TODO: define better way to determine depth?
        return 23


if __name__ == '__main__':
    pass
