import numpy as np
import os
import pandas as pd
from laspy.file import File
import logging
import time


logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
las_dir = r'I:\NGS_TPU\DATA\FL1604-TB-N\las'
las_files = [os.path.join(las_dir, l) for l in os.listdir(las_dir) if l.endswith('.las')]
total_tic = time.time()
class_codes = {'BATHYMETRY': 26}
bathy_points = None

for las in sorted(las_files)[20:30]:
    print las,
    inFile = File(las, mode="r")
    num_pts = inFile.__len__()
    print '({} points)'.format(num_pts)
    bathy_inds = np.empty(num_pts, dtype=bool)
    start_ind = 0
    end_ind = 0
    all_pnt_classes = inFile.raw_classification
    chunks = np.array_split(all_pnt_classes, 10)

    flight_line_ids = np.unique(bathy_points['pt_src_id'])
    print flight_line_ids
    for fl in flight_line_ids:
        print 'getting bathy points...'
        for c, chunk in enumerate(chunks):
            bathy_inds = np.empty(num_pts, dtype=bool)
            start_ind = end_ind
            end_ind += chunk.shape[0]
            inds = chunk == class_codes['BATHYMETRY']

            bathy_inds[start_ind:end_ind] = inds
            bathy_records = inFile.points[bathy_inds]
            bathy_points = bathy_records['point']

            flight_lines = bathy_points['pt_src_id'] == fl
            flight_line_bathy = bathy_points[flight_lines]

        flight_line_bathy_sorted = np.sort(flight_line_bathy, order='gps_time')

            print fl
            print flight_line_bathy_sorted[0:5:]



print 'TOTAL TIME:', time.time() - total_tic
