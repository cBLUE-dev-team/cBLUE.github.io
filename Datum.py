class Datum:
    def __init__(self):
        pass

    def get_vdatum_region_mcus(self):
        vdatum_regions_MCU_file = r'V_Datum_MCU_Values.txt'
        vdatum_regions_file_obj = open(vdatum_regions_MCU_file, 'r')
        vdatum_regions = vdatum_regions_file_obj.readlines()
        vdatum_regions_file_obj.close()

        # clean up vdatum file; when copying table from internet, some dashes
        # are 'regular dashes' and others are \x96; get rid of quotes and \n
        default_msg = '---No Region Specified---'
        vdatum_regions = [v.replace('\x96', '-') for v in vdatum_regions]
        vdatum_regions = [v.replace('"', '') for v in vdatum_regions]
        vdatum_regions = [v.replace('\n', '') for v in vdatum_regions]
        regions = [v.split('\t')[0] for v in vdatum_regions]
        mcu_values = [v.split('\t')[1] for v in vdatum_regions]

        return regions, mcu_values, default_msg


if __name__ == '__main__':
    pass
