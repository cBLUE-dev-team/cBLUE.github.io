"""
cBLUE (comprehensive Bathymetric Lidar Uncertainty Estimator)
Copyright (C) 2019 
Oregon State University (OSU)
Center for Coastal and Ocean Mapping/Joint Hydrographic Center, University of New Hampshire (CCOM/JHC, UNH)
NOAA Remote Sensing Division (NOAA RSD)

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 2.1 of the License, or (at your option) any later version.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this library; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

Contact:
Christopher Parrish, PhD
School of Construction and Civil Engineering
101 Kearney Hall
Oregon State University
Corvallis, OR  97331
(541) 737-5688
christopher.parrish@oregonstate.edu

"""

import logging
logging.basicConfig(format='%(asctime)s:%(message)s', level=logging.INFO)
import pathos.pools as pp
import json
import os
import sys
import laspy
import numpy as np
import numexpr as ne
import pandas as pd
import progressbar
from tqdm import tqdm
from collections import OrderedDict
from Merge import Merge
from Subaerial import Subaerial, SensorModel, Jacobian
from Subaqueous import Subaqueous
from Las import Las
import datetime
import cProfile


class Tpu:
    """
    This class coordinates the TPU workflow.  Beginning when the user 
    hits *Compute TPU*, the general workflow is summarized below:

    1. Form observation equation (SensorModel class)
    2. Generate Jacobian (Jacobian class)
    3. for each flight line within Las

        * Merge the Las data and trajectory data (Merge class)
        * Calculate subaerial THU and TVU (Subaerial class)
        * Calculate subaqueous THU and TVU (Subaqueous class)
        * Combine subaerial and subaqueous TPU
        * Export TPU (either as Python "pickle' or as Las extra bytes)
    
    Currently, the following options are hard coded, but development 
    plans include adding user-configurable options in a settings menu
    within the GUI:

    * Whether the TPU is exported as a Python binary pickle file or as TPU extra bytes within a Las file
    * Whether step three is run as either single- or multi-processing    
    """

    def __init__(self, surface_select, surface_ind,
                 wind_selection, wind_val,
                 kd_selection, kd_val, vdatum_region,
                 vdatum_region_mcu, tpu_output, cblue_version, 
                 sensor_model, cpu_process_info):

        # TODO: refactor to pass the GUI object, not individual variables (with controller?)
        self.cblue_version = cblue_version
        self.sensor_model = sensor_model
        self.cpu_process_info = cpu_process_info
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

        :param sbet_las_tile: generator yielding sbet data and las tile name for each las tile
        :return:
        """

        sbet, las_file = sbet_las_files

        data_to_pickle = []
        output_columns = []

        # FORM OBSERVATION EQUATIONS
        S = SensorModel(self.sensor_model)

        # GENERATE JACOBIAN FOR SENSOR MODEL OBSVERVATION EQUATIONS
        J = Jacobian(S)

        # FORM LAS OBJECT TO ACCESS INFORMATION IN LAS FILE
        las = Las(las_file)

        # FORM OBJECT THAT PROVIDES FUNCTIONALITY TO MERGE LAS AND TRAJECTORY DATA
        M = Merge()

        logging.info('{} {} ({:,} points)'.format(las.las_short_name, '#' * 30, las.num_file_points))
        logging.info(las.get_flight_line_ids())
        las_xyzt, t_sort_indx, flight_lines = las.get_flight_line_txyz()
        
        for fl in las.get_flight_line_ids():

            logging.info('flight line {} {}'.format(fl, '-' * 50))

            # las_xyzt has the same order as self.points_to_process
            flight_line_indx = flight_lines == fl
            fl_sorted_las_xyzt = las_xyzt[t_sort_indx][flight_line_indx[t_sort_indx]]

            # CREATE MERGED-DATA OBJECT M
            logging.info('({}) merging trajectory and las data...'.format(las.las_short_name))
            merged_data, stddev = M.merge(las.las_short_name, fl, sbet.values, fl_sorted_las_xyzt)
            toc = datetime.datetime.now()

            if merged_data is not False:  # i.e., las and sbet is merged

                logging.info('({}) calculating subaer THU/TVU...'.format(las.las_short_name))
                subaer_obj = Subaerial(J, merged_data, stddev)
                subaer_thu, subaer_tvu, subaer_cols = subaer_obj.calc_subaerial_tpu()
                depth = merged_data[4] + las.get_average_water_surface_ellip_height()

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
                output = np.vstack((
                    np.expand_dims(merged_data[1], axis=0),  # las_t
                    #np.round_(np.expand_dims(subaer_thu, axis=0), decimals=5),
                    #np.round_(np.expand_dims(subaer_tvu, axis=0), decimals=5),
                    #np.round_(np.expand_dims(subaqu_thu, axis=0), decimals=5),
                    #np.round_(np.expand_dims(subaqu_tvu, axis=0), decimals=5),
                    np.round_(np.expand_dims(total_thu, axis=0), decimals=5),
                    np.round_(np.expand_dims(total_tvu, axis=0), decimals=5),
                    )).T

                sigma_columns = ['total_thu', 'total_tvu']

                # TODO: doesn't need to happen every iteration
                #output_columns = ['gps_time'] + subaer_cols + subaqu_cols + sigma_columns
                output_columns = ['gps_time'] + sigma_columns

                data_to_pickle.append(output)
                stats = ['min', 'max', 'mean', 'std']
                decimals = pd.Series([15] + [3] * len(sigma_columns), index=output_columns)
                df = pd.DataFrame(output, columns=output_columns).describe().loc[stats]
                self.flight_line_stats[str(fl)] = df.round(decimals).to_dict()

            else:
                logging.warning('SBET and LAS not merged because max delta '
                                'time exceeded acceptable threshold of {} '
                                'sec(s).'.format(Merge.max_allowable_dt))

        self.write_metadata(las)  # TODO: include as VLR?
        self.output_tpu_to_las_extra_bytes(las, data_to_pickle, output_columns)
        #self.output_tpu_to_pickle(las, data_to_pickle, output_columns)

    def output_tpu_to_pickle(self, las, data_to_output, output_columns):
        """output the calculated tpu to a Python "pickle" file

        This method outputs the calculated tpu to a Python "pickle" file, with the
        following fields:

        .. csv-table:: Data Pickle...mmmm
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
        decimals = pd.Series([2] * len(output_df.columns), index=output_columns)
        output_df = output_df.round(decimals) * 100
        output_df = output_df.astype('uint8')  # uint8 = numpy Unsigned integer (0 to 255)

        out_las_name = os.path.join(self.tpuOutput, las.las_base_name) + '_TPU.las'
        logging.info('logging las and tpu results to {}'.format(out_las_name))
        in_las = laspy.file.File(las.las, mode="r")  # las is Las object
        out_las = laspy.file.File(out_las_name, mode="w", header=in_las.header)

        xy_data_type = 7  # 7 = laspy unsigned long long (8 bytes)
        z_data_type = 6  # 6 = laspy long (4 bytes)
        tpu_data_type = 2  # 2 = laspy char (1 byte)

        extra_byte_dimensions = OrderedDict([
            #('cblue_x', ('calculated x', xy_data_type)),
            #('cblue_y', ('calculated y', xy_data_type)),
            #('cblue_z', ('calculated z', z_data_type)),
            #('subaerial_thu', ('subaerial thu', tpu_data_type)),
            #('subaerial_tvu', ('subaerial tvu', tpu_data_type)),
            #('subaqueous_thu', ('subaqueous thu', tpu_data_type)),
            #('subaqueous_tvu', ('subaqueous tvu', tpu_data_type)),
            ('total_thu', ('total thu', tpu_data_type)),
            ('total_tvu', ('total tvu', tpu_data_type)),
            ])

        # define new extrabyte dimensions
        for dimension, description in extra_byte_dimensions.items():
            logging.info('creating extra byte dimension for {}...'.format(dimension))
            out_las.define_new_dimension(
                name=dimension, 
                data_type=description[1], 
                description=description[0])

        '''
        using eval to do following with a loop, versus explicityly
        defining each one, takes too long because lists are made
        '''

        #logging.info('populating extra byte data for cblue_x...')
        #out_las.cblue_x = output_df['cblue_x']

        #logging.info('populating extra byte data for cblue_y...')
        #out_las.cblue_y = output_df['cblue_y']
        
        #logging.info('populating extra byte data for cblue_z...')
        #out_las.cblue_z = output_df['cblue_z']
        
        #logging.info('populating extra byte data for subaerial_thu...')
        #out_las.subaerial_thu = output_df['subaerial_thu']
        
        #logging.info('populating extra byte data for subaerial_tvu...')
        #out_las.subaerial_tvu = output_df['subaerial_tvu']
        
        #logging.info('populating extra byte data for subaqueous_thu...')
        #out_las.subaqueous_thu = output_df['subaqueous_thu']
        
        #logging.info('populating extra byte data for subaqueous_tvu...')
        #out_las.subaqueous_tvu = output_df['subaqueous_tvu']
        
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
            'flight line stats': {},
            'sensor model': self.sensor_model,
            'cBLUE version': self.cblue_version,
            'cpu_processing_info': self.cpu_process_info, 
        })

        try:
            self.metadata['flight line stats'].update(self.flight_line_stats)  # flight line metadata
            with open(os.path.join(self.tpuOutput, '{}.json'.format(las.las_base_name)), 'w') as outfile:
                json.dump(self.metadata, outfile, indent=1, ensure_ascii=False)
        except Exception as e:
            logging.error(e)
            print(e)

    def run_tpu_multiprocess(self, num_las, sbet_las_generator):
        """runs the tpu calculations using multiprocessing

        This methods initiates the tpu calculations using the pathos multiprocessing
        framework (https://pypi.org/project/pathos/).  Whether the tpu calculations
        are done with multiprocessing or not is currently determined by which
        "run_tpu_*" method is manually specified in the tpu_process_callback()
        method of the CBlueApp class.  TODO: Include
        a user option to select single processing or multiprocessing

        :param sbet_las_generator:
        :return:
        """

        print('Calculating TPU...')
        p = pp.ProcessPool(4)

        for _ in tqdm(p.imap(self.calc_tpu, sbet_las_generator), total=num_las, ascii=True):
            pass

        p.close()
        p.join()


    def run_tpu_singleprocess(self, num_las, sbet_las_generator):
        """runs the tpu calculations using a single processing

        This methods initiates the tpu calculations using single processing.
        Whether the tpu calculations are done with multiprocessing or not is
        currently determined by which "run_tpu_*" method is manually specified
        the tpu_process_callback() method of the CBlueApp class.  TODO: Include
        a user option to select single processing or multiprocessing

        :param sbet_las_generator:
        :return:
        """

        print('Calculating TPU...')
        with progressbar.ProgressBar(max_value=num_las) as bar:
            for i, sbet_las in enumerate(sbet_las_generator):
                bar.update(i)
                self.calc_tpu(sbet_las)


if __name__ == '__main__':
    pass
