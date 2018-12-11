import laspy
from collections import OrderedDict

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

# Set up our input and output files.
inFile = laspy.file.File(r"C:\QAQC_contract\marco_island\2016_429500e_2870000n_TPU.las", mode = "r")

headerformat = inFile.header.header_format
for spec in headerformat:
    print(spec.name)
    
point_records = inFile.points
print(point_records)

for dim in extra_byte_dimensions:
    print(inFile.reader.get_dimension(dim))
