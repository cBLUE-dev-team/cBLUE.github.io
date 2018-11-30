import laspy



# Set up our input and output files.
inFile = laspy.file.File(r"C:\QAQC_contract\marco_island\2016_429500e_2868500n.las", mode = "r")
outFile = laspy.file.File(r"C:\QAQC_contract\marco_island\2016_429500e_2868500n_COPY.las", mode = "w",
			header = inFile.header)

# Define our new dimension. Note, this must be done before giving
# the output file point records.
outFile.define_new_dimension(name="my_special_dimension",
						data_type=5, description="Test Dimension")

# Lets go ahead and copy all the existing data from inFile:
for dimension in inFile.point_format:
	print('writing {} to {} ...'.format(dimension.name, outFile))
	dat = inFile.reader.get_dimension(dimension.name)
	outFile.writer.set_dimension(dimension.name, dat)

# Now lets put data in our new dimension
# (though we could have done this first)

# Note that the data type 5 refers to a long integer
outFile.my_special_dimension = range(len(inFile))


headerformat = outFile.header.header_format
for spec in headerformat:
	print(spec.name)


point_records = inFile.points
print(point_records)
print(outFile.reader.get_dimension('my_special_dimension'))
