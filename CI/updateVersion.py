import sys
import re

FILE_WITH_VERSION_INFORMATIONS = "version"

if len(sys.argv) != 2:
    print("""Problem with argument.\n
             Expected exactly one argument with new version number - e.g. '1.23.0.0'""")
    exit(1)

new_version = sys.argv[1]

if re.match(r"[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+", new_version) == None:
    print("Wrong format of argument:", new_version,
          "\nRequired format: 1.23.0.0")
    exit(1)

new_version_commas = new_version.replace('.', ', ')

# Read data from template file
fin = open(FILE_WITH_VERSION_INFORMATIONS + "_template.py", "rt")
data = fin.read()
data = data.replace('filevers=(78, 0, 3904, 108)',
                    'filevers=(' + new_version_commas + ')')
data = data.replace('prodvers=(78, 0, 3904, 108)',
                    'prodvers=(' + new_version_commas + ')')
data = data.replace("u'FileVersion', u'78, 0, 3904, 108'",
                    "u'FileVersion', u'" + new_version + "'")
data = data.replace("u'ProductVersion', u'78, 0, 3904, 108'",
                    "u'ProductVersion', u'" + new_version + "'")
fin.close()

# Write the data to new output file
fin = open(FILE_WITH_VERSION_INFORMATIONS + ".py", "wt")
fin.write(data)
fin.close()

print(sys.argv[0], "- version updated to:", new_version)