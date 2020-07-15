# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx
VSVersionInfo(
  ffi=FixedFileInfo(
    # filevers and prodvers should be always a tuple with four items: (1, 2, 3, 4)
    # Set not needed items to zero 0.
    filevers=(2, 2, 1, 0),
    prodvers=(2, 2, 1, 0),
    # Contains a bitmask that specifies the valid bits 'flags'r
    mask=0x17,
    # Contains a bitmask that specifies the Boolean attributes of the file.
    flags=0x0,
    # The operating system for which this file was designed.
    # 0x4 - NT and there is no need to change it.
    OS=0x4,
    # The general type of file.
    # 0x1 - the file is an application.
    fileType=0x1,
    # The function of the file.
    # 0x0 - the function is not defined for this fileType
    subtype=0x0,
    # Creation date and time stamp.
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904b0',
        [StringStruct(u'CompanyName', u'NOAA NGS RSD'),
        StringStruct(u'FileDescription', u'cBlue'),
        StringStruct(u'FileVersion', u'2, 2, 1, 0'),
        StringStruct(u'InternalName', u'cBlue'),
        StringStruct(u'LegalCopyright', u'LGPL-2.1'),
        StringStruct(u'OriginalFilename', u'cBlue.exe'),
        StringStruct(u'ProductName', u'cBlue'),
        StringStruct(u'ProductVersion', u'2.2.1.0'),
        StringStruct(u'CompanyShortName', u'NOAA'),
        StringStruct(u'ProductShortName', u'cBlue'),
        StringStruct(u'LastChange', u'045304945a791ebf8850ddc90c2814b7d04b6d0c'),
        StringStruct(u'Official Build', u'2.2.1-rc2')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)