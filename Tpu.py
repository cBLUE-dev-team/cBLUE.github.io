import logging
logging.basicConfig(format='%(asctime)s:%(message)s', level=logging.INFO)
import pathos.pools as pp
import json
import os
import laspy
import numpy as np
import numexpr as ne
import pandas as pd
from collections import OrderedDict
from Las import Las
from Merge import Merge
from Subaerial import Subaerial
from Subaqueous import Subaqueous


class Tpu:

    def __init__(self, surface_select, surface_ind,
                 wind_selection, wind_val,
                 kd_selection, kd_val, vdatum_region,
                 vdatum_region_mcu, tpu_output):
        self.subaqu_lookup_params = None
        self.surface_select = surface_select
        self.surface_ind = surface_ind
        self.wind_selection = wind_selection
        self.wind_val = wind_val
        self.kd_selection = kd_selection
        self.kd_val = kd_val
        self.vdatum_region = vdatum_region
        self.vdatum_region_mcu = vdatum_region_mcu
        self.tpuOutput = tpu_output
        self.metadata = {}
        self.flight_line_stats = {}

    def calc_tpu(self, sbet_las_files):
        """

        :param sbet_las_tile:
        :return:
        """

        sbet, las = sbet_las_files

        data_to_pickle = []
        output_columns = []

        las = Las(las)
        logging.info('{}\n{}'.format('#' * 30, las.las_short_name))
        logging.info(las.get_flight_line_ids())

        for fl in las.get_flight_line_ids():
            logging.info('flight line {} {}'.format(fl, '-' * 30))
            D = Merge.merge(las.las_short_name, fl, sbet.values, las.get_flight_line_txyz(fl))

            logging.info('({}) calculating subaer THU/TVU...'.format(las.las_short_name))
            subaer, subaer_cols = Subaerial(D).calc_subaerial_tpu()
            depth = subaer[:, 2] + las.get_average_water_surface_ellip_height()
            subaer_thu = subaer[:, 3]
            subaer_tvu = subaer[:, 4]

            logging.info('({}) calculating subaqueous THU/TVU...'.format(las.las_short_name))
            subaqu_obj = Subaqueous(self.surface_ind, self.wind_val, self.kd_val, depth)
            subaqu_thu, subaqu_tvu, subaqu_cols = subaqu_obj.fit_lut()
            self.subaqu_lookup_params = subaqu_obj.get_subaqueous_meta_data()
            vdatum_mcu = float(self.vdatum_region_mcu) / 100.0  # file is in cm (1-sigma)

            logging.info('({}) calculating total THU...'.format(las.las_short_name))
            total_thu = ne.evaluate('sqrt(subaer_thu**2 + subaqu_thu**2)')

            logging.info('({}) calculating total TVU...'.format(las.las_short_name))
            total_tvu = ne.evaluate('sqrt(subaqu_tvu**2 + subaer_tvu**2 + vdatum_mcu**2)')
            num_points = total_tvu.shape[0]
            output = np.hstack((
                np.expand_dims(D[1], axis=1),  # las time
                np.round_(subaer, decimals=5),
                np.round_(np.expand_dims(subaqu_thu, axis=1), decimals=5),
                np.round_(np.expand_dims(subaqu_tvu, axis=1), decimals=5),
                np.round_(np.expand_dims(total_thu, axis=1), decimals=5),
                np.round_(np.expand_dims(total_tvu, axis=1), decimals=5),
                ))

            sigma_columns = ['total_thu', 'total_tvu']

            # TODO: doesn't need to happen every iteration
            output_columns = ['gps_time'] + subaer_cols + subaqu_cols + sigma_columns

            data_to_pickle.append(output)
            stats = ['min', 'max', 'mean', 'std']
            decimals = pd.Series([15] + [3] * (len(output_columns) - 1), index=output_columns)
            df = pd.DataFrame(output, columns=output_columns).describe().loc[stats]
            self.flight_line_stats[str(fl)] = df.round(decimals).to_dict()

        self.write_metadata(las)  # TODO: include as VLR?
        # self.output_tpu_to_las_extra_bytes(las, data_to_pickle, output_columns)
        self.output_tpu_to_pickle(las, data_to_pickle, output_columns)

    def output_tpu_to_pickle(self, las, data_to_output, output_columns):
        """output the calculated tpu to a Python "pickle" file

        This method outputs the calculated tpu to a Python "pickle" file, with the
        following fields:

        .. csv-table:: Frozen Delights!
            :header: index, ndarray, description
            :widths: 14, 20, 20

            0, gps_time, GPS standard adjusted time
            1, cblue_x, cBLUE-calculated x coordinate
            2, cblue_y, cBLUE-calculated y coordinate
            3, cblue_z, cBLUE-calculated z coordinate
            4, subaerial_thu, subaerial total horizontal uncertainty
            5, subaerial_tvu, subaerial total vertical uncertainty
            6, subaqueous_thu, subaqueous total horizontal uncertainty
            7, subaqueous_tvu, subaqueous total vertical uncertainty
            8, total_thu, total horizontal uncertainty
            9, total_tvu, otal vertical uncertainty

        :param las:
        :param data_to_output:
        :param output_columns:
        :return: n/a
        """
        output_tpu_file = r'{}_TPU.tpu'.format(las.las_base_name)
        output_path = '{}\\{}'.format(self.tpuOutput, output_tpu_file)
        output_df = pd.DataFrame(np.vstack(data_to_output), columns=output_columns)
        logging.info('({}) writing TPU...'.format(las.las_short_name))
        output_df.to_pickle(output_path)
        logging.info('finished writing')

    def output_tpu_to_las_extra_bytes(self, las, data_to_output, output_columns):
        """output the calculated tpu to a las file

        This method creates a las file tht contains the contents of the
        original las file and the calculated tpu values as VLR extra bytes.
        The las file is generated using "The laspy way", as documented in
        https://laspy.readthedocs.io/en/latest/tut_part_3.html.

        The following references have additional information describing las
        extra bytes:

        LAS v1.4 specifications:
        https://www.asprs.org/a/society/committees/standards/LAS_1_4_r13.pdf

        The LAS 1.4 Specification (ASPRS PERS article)
        https://www.asprs.org/wp-content/uploads/2010/12/LAS_Specification.pdf

        ASPRS LAS Working Group Github repository
        https://github.com/ASPRSorg/LAS

        The following table lists the information contained as extra bytes:

        .. csv-table:: cBLUE VLR Extra Bytes
            :header: id, dtype, description
            :widths: 14, 20, 20

            cblue_x, unsigned long long (8 bytes), cBLUE-calculated x coordinate
            cblue_y, unsigned long long (8 bytes), cBLUE-calculated y coordinate
            cblue_z, long (4 bytes), cBLUE-calculated z coordinate
            subaerial_thu, unsigned short (2 bytes), subaerial total horizontal uncertainty
            subaerial_tvu, unsigned short (2 bytes), subaerial total vertical uncertainty
            subaqueous_thu, unsigned short (2 bytes), subaqueous total horizontal uncertainty
            subaqueous_tvu, unsigned short (2 bytes), subaqueous total vertical uncertainty
            total_thu,  unsigned short (2 bytes), total horizontal uncertainty
            total_tvu,  unsigned short (2 bytes), total vertical uncertainty

        :param las:
        :param data_to_output:
        :param output_columns:
        :return:
        """
        output_df = pd.DataFrame(np.vstack(data_to_output), columns=output_columns)
        output_df = output_df.sort_values(by=['gps_time'])
        decimals = pd.Series([3] * len(output_df.columns), index=output_columns)
        output_df = output_df.round(decimals) * 1000
        output_df = output_df.astype('int64')

        out_las_name = os.path.join(self.tpuOutput, las.las_base_name) + '_TPU.las'
        logging.info('logging las and tpu results to {}'.format(out_las_name))
        in_las = laspy.file.File(las.las, mode="r")  # las is Las object
        out_las = laspy.file.File(out_las_name, mode="w", header=in_las.header)

        xy_data_type = 7  # 7 = laspy unsigned long long (8 bytes)
        z_data_type = 6  # 6 = laspy long (4 bytes)
        tpu_data_type = 3  # 3 = laspy unsigned short (2 bytes)

        extra_byte_dimensions = OrderedDict([
            ('cblue_x', ('calculated x', xy_data_type)),
            ('cblue_y', ('calculated y', xy_data_type)),
            ('cblue_z', ('calculated z', z_data_type)),
            ('subaerial_thu', ('subaerial thu', tpu_data_type)),
            ('subaerial_tvu', ('subaerial tvu', tpu_data_type)),
            ('subaqueous_thu', ('subaqueous thu', tpu_data_type)),
            ('subaqueous_tvu', ('subaqueous tvu', tpu_data_type)),
            ('total_thu', ('total thu', tpu_data_type)),
            ('total_tvu', ('total tvu', tpu_data_type)),
            ])

        # define new extrabyte dimensions
        for dimension, description in extra_byte_dimensions.iteritems():
            logging.info('creating extra byte dimension for {}...'.format(dimension))
            out_las.define_new_dimension(
                name=dimension, 
                data_type=description[1], 
                description=description[0])

        logging.info('populating extra byte data for cblue_x...')
        out_las.cblue_x = output_df['cblue_x']

        logging.info('populating extra byte data for cblue_y...')
        out_las.cblue_y = output_df['cblue_y']
        
        logging.info('populating extra byte data for cblue_z...')
        out_las.cblue_z = output_df['cblue_z']
        
        logging.info('populating extra byte data for subaerial_thu...')
        out_las.subaerial_thu = output_df['subaerial_thu']
        
        logging.info('populating extra byte data for subaerial_tvu...')
        out_las.subaerial_tvu = output_df['subaerial_tvu']
        
        logging.info('populating extra byte data for subaqueous_thu...')
        out_las.subaqueous_thu = output_df['subaqueous_thu']
        
        logging.info('populating extra byte data for subaqueous_tvu...')
        out_las.subaqueous_tvu = output_df['subaqueous_tvu']
        
        logging.info('populating extra byte data for total_thu...')
        out_las.total_thu = output_df['total_thu']
        
        logging.info('populating extra byte data for total_tvu...')
        out_las.total_tvu = output_df['total_tvu']

        # copy data from in_las
        for field in in_las.point_format:
            logging.info('writing {} to {} ...'.format(field.name, out_las))
            dat = in_las.reader.get_dimension(field.name)
            out_las.writer.set_dimension(field.name, dat[las.time_sort_indices])

    def write_metadata(self, las):
        """creates a json file with summary statistics and metedata

        This method creates a json file containing summary statistics for each
        tpu field, per flight line, and a record of the environmental and VDatum
        parameters specified by the user.  The file also records certain
        parameters used during the monte carlo simulations used to create
        the lookup tables used in the subaqueous portion of the tpu calculations.

        :param las:
        :return: n/a
        """
        logging.info('({}) creating TPU meta data file...'.format(las.las_short_name))
        self.metadata.update({
            'subaqueous lookup params': self.subaqu_lookup_params,
            'water surface': self.surface_select,
            'wind': self.wind_selection,
            'kd': self.kd_selection,
            'VDatum region': self.vdatum_region,
            'VDatum region MCU': self.vdatum_region_mcu,
            'flight line stats': {}
        })

        try:
            self.metadata['flight line stats'].update(self.flight_line_stats)  # flight line metadata
            with open(os.path.join(self.tpuOutput, '{}.json'.format(las.las_base_name)), 'w') as outfile:
                json.dump(self.metadata, outfile, indent=1, ensure_ascii=False)
        except Exception, e:
            print(e)

    def run_tpu_multiprocess(self, sbet_las_generator):
        """runs the tpu calculations using multiprocessing

        This methods initiates the tpu calculations using the pathos multiprocessing
        framework (https://pypi.org/project/pathos/).  Whether the tpu calculations
        are done with multiprocessing or not is currently determined by which
        "run_tpu_*" method is manually specified in the tpu_process_callback()
        method of the CBlueApp class.  Including a user option to select single
        processing or multiprocessing is deferred to future versions.

        :param sbet_las_generator:
        :return:
        """
        p = pp.ProcessPool()
        p.map(self.calc_tpu, sbet_las_generator)
        p.close()
        p.join()

    def run_tpu_singleprocess(self, sbet_las_generator):
        """runs the tpu calculations using a single processing

        This methods initiates the tpu calculations using single processing.
        Whether the tpu calculations are done with multiprocessing or not is
        currently determined by which "run_tpu_*" method is manually specified
        the tpu_process_callback() method of the CBlueApp class.  Including
        a user option to select single processing or multiprocessing is
        deferred to a future version.

        :param sbet_las_generator:
        :return:
        """
        for sbet_las in sbet_las_generator:
            self.calc_tpu(sbet_las)


if __name__ == '__main__':
    pass
