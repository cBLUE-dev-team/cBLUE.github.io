import laspy
from collections import OrderedDict
import os

xy_data_type = 7  # 10 = laspy unsigned long long (8 bytes)
z_data_type = 5  # 5 = laspy unsigned long (4 bytes)
tpu_data_type = 5

extra_byte_dimensions = OrderedDict([
    ('cblue_x', ('calculated x', xy_data_type)),
    ('cblue_y', ('calculated y', xy_data_type)),
    ('cblue_z', ('calculated z', z_data_type)),
    ('subaerial_thu', ('subaerial thu', tpu_data_type)),
    ('subaerial_tvu', ('subaerial tvu', tpu_data_type)),
    ('subaqueous_thu', ('subaqueous thu', tpu_data_type)),
    ('subaqueous_tvu', ('subaqueous tvu', tpu_data_type)),
    ('total_thu', ('total thu', tpu_data_type)),
    ('total_tvu', ('total tvu', tpu_data_type))
    ])

las_dir = r'C:\Users\nickf\OneDrive\OSU_PhD\OSU_Parrish_Forfinski_Share\DATA\ouput'

las_files = [os.path.join(las_dir, l) for l in os.listdir(las_dir) if l.endswith('_HEADER.las')]

# Set up our input and output files.
inFile = laspy.file.File(las_files[0], mode="r")

headerformat = inFile.header.header_format
for spec in headerformat:
    print(spec.name),
    print(inFile.header.reader.get_header_property(spec.name))
    
point_records = inFile.points
print(point_records)

# for dim in extra_byte_dimensions:
#     print(dim),
#     print(inFile.reader.get_dimension(dim))

print inFile.extra_bytes

