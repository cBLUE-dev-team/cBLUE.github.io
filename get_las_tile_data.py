from laspy.file import File
import pathos.pools as pp
import numpy as np
import os
import time


class Las:

    def __init__(self):
        self.name = 3

    def get_las(self, las):
        from laspy.file import File
        import numpy as np

        print las
        self.name = 2
        inFile = File(las, mode="r")
        class_codes = {'BATHYMETRY': 26}
        bathy_inds = inFile.raw_classification == class_codes['BATHYMETRY']
        bathy_points = inFile.points[bathy_inds]['point']
        flight_line_ids = np.unique(bathy_points['pt_src_id'])

        for fl in flight_line_ids:
            print '{}...'.format(fl)
            flight_line_indx = bathy_points['pt_src_id'] == fl
            flight_line_bathy = bathy_points[flight_line_indx]
            flight_line_bathy_sorted = np.sort(flight_line_bathy, order='gps_time')
            print flight_line_bathy_sorted[0:1]

    def run(self):
        las_dir = r'I:\NGS_TPU\DATA\FL1604-TB-N\las'
        las_files = [os.path.join(las_dir, l) for l in os.listdir(las_dir) if l.endswith('.las')]
        total_tic = time.time()

        p = pp.ProcessPool()
        p.map(self.get_las, las_files[20:30])
        p.close()
        p.join()
        print 'TOTAL TIME:', time.time() - total_tic


if __name__ == '__main__':
    l = Las()
    l.run()

