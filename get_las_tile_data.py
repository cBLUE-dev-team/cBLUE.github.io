import numpy as np
import time
from laspy.file import File

las = r'I:\NGS_TPU\DATA\FL1604-TB-N\las\2016_429500e_2865500n - Copy.las'
inFile = File(las, mode="r")

tic = time.time()

print 'extracting bathy...'
all_pnt_classes = inFile.raw_classification
bathy_class = all_pnt_classes == 26
bathy_records = inFile.points[bathy_class]
bathy_points = bathy_records['point']
print bathy_points

flight_line_ids = np.unique(bathy_points['pt_src_id'])
for fl in flight_line_ids:
    flight_lines = bathy_points['pt_src_id'] == fl
    flight_line_bathy = bathy_points[flight_lines]
    flight_line_bathy_sorted = np.sort(flight_line_bathy, order='gps_time')
    print flight_line_bathy_sorted

toc = time.time()
print toc - tic
#
# tic = time.time()
# pts = inFile.points['point']
# print 'extracting bathy...'
# bathy_pts = pts[inFile.raw_classification == 26]
#
# flight_line_ids = np.unique(bathy_pts['pt_src_id'])
# for fl in flight_line_ids:
#     flight_lines = bathy_pts['pt_src_id'] == fl
#     flight_line_bathy = bathy_pts[flight_lines]
#     flight_line_bathy_sorted = np.sort(flight_line_bathy, order='gps_time')
#     print flight_line_bathy_sorted
#
#
# toc = time.time()
#
# print toc - tic

