import laspy
from collections import OrderedDict

extra_byte_dimensions = OrderedDict([
    ('subaerial_thu', 'subaerial thu'),
    ('subaerial_tvu', 'subaerial tvu'),
    ('subaqueous_thu', 'subaqueous thu'),
    ('subaqueous_tvu', 'subaqueous tvu'),
    ('total_thu', 'total thu'),
    ('total_tvu', 'total tvu')
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
