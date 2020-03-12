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
from pathlib import Path
from pathos import logger
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
from Subaerial import Subaerial
from Subaqueous import Subaqueous
from Las import Las
import datetime
import cProfile

import matplotlib.pyplot as plt


class Tpu:
    """
    TODO:  rework...becasue J & M moved to CBlueApp.py
    This class coordinates the TPU workflow.  Beginning when the user 
    hits *Compute TPU*, the general workflow is summarized below:

    1. Form observation equation (SensorModel class)
    2. Generate Jacobian (Jacobian class)
    3. for each flight line within Las

        * Merge the Las data and trajectory data (Merge class)
        * Calculate subaerial thu and tvu (Subaerial class)
        * Calculate subaqueous thu and tvu (Subaqueous class)
        * Combine subaerial and subaqueous TPU
        * Export TPU (either as Python "pickle' or as Las extra bytes)
    
    """

    def __init__(self, surface_select, surface_ind,
                 wind_selection, wind_val,
                 kd_selection, kd_val, vdatum_region,
                 vdatum_region_mcu, tpu_output, cblue_version, 
                 sensor_model, cpu_process_info, subaqueous_luts,
                 water_surface_ellipsoid_height):

        # TODO: refactor to pass the GUI object, not individual variables (with controller?)
        self.surface_select = surface_select
        self.surface_ind = surface_ind
        self.wind_selection = wind_selection
        self.wind_val = wind_val
        self.kd_selection = kd_selection
        self.kd_val = kd_val
        self.vdatum_region = vdatum_region
        self.vdatum_region_mcu = vdatum_region_mcu
        self.tpu_output = tpu_output
        self.cblue_version = cblue_version
        self.sensor_model = sensor_model
        self.cpu_process_info = cpu_process_info
        self.subaqueous_luts = subaqueous_luts
        self.water_surface_ellipsoid_height = water_surface_ellipsoid_height

        self.subaqu_lookup_params = None
        self.metadata = {}
        self.flight_line_stats = {}

    def update_fl_stats(self, fl, num_fl_points, fl_tpu_data):

        # calc flight line tpu summary stats
        fl_tpu_count = fl_tpu_data.shape[0]
        fl_tpu_min = fl_tpu_data[:, 0:6].min(axis=0).tolist()
        fl_tpu_max = fl_tpu_data[:, 0:6].max(axis=0).tolist()
        fl_tpu_mean = fl_tpu_data[:, 0:6].mean(axis=0).tolist()
        fl_tpu_stddev = fl_tpu_data[:, 0:6].std(axis=0).tolist()

        fl_stat_indx = {
            'total_thu': 0,
            'total_tvu': 1,
            }

        fl_stats_strs = []
        for fl_stat, ind in fl_stat_indx.items():
            fl_stats_vals = (fl_stat,
                             fl_tpu_min[ind], 
                             fl_tpu_max[ind],
                             fl_tpu_mean[ind], 
                             fl_tpu_stddev[ind])
        
            fl_stats_str = '{}: {:6.3f}{:6.3f}{:6.3f}{:6.3f}'.format(*fl_stats_vals)
            #fl_stats_str = '{}: {:6d}{:6d}{:6.0f}{:6.0f}'.format(*fl_stats_vals)
            fl_stats_strs.append(fl_stats_str)

        fl_header_str = f'{fl} ({fl_tpu_count}/{num_fl_points} points with TPU)'
        self.flight_line_stats.update({fl_header_str: fl_stats_strs})

    def export_diag_data(self, las_base_name, diag_dfs):
        diag_data_fields = {
            'las_data': [
                'las_name', 
                'flight_line', 
                'raw_class',
                'las_t', 
                'las_x', 
                'las_y', 
                'las_z'],
            'sbet_data': [
                'sbet_t', 
                'sbet_x', 
                'sbet_y', 
                'sbet_z', 
                'r', 
                'p', 
                'h', 
                'std_r', 
                'std_p', 
                'std_h', 
                'stdx_sbet', 
                'stdy_sbet', 
                'stdz_sbet'],
            'subaerial_data': [
                'rho_est', 
                'a_est', 
                'b_est', 
                'std_a', 
                'std_b', 
                'std_rho', 
                'aer_x_pre_poly', 
                'aer_y_pre_poly', 
                'aer_z_pre_poly', 
                'dx', 
                'dy', 
                'dz'],
            'cblue_position': [
                'cblue_aer_x', 
                'cblue_aer_y', 
                'cblue_aer_z', 
                'cblue_aer_err_x', 
                'cblue_aer_err_y', 
                'cblue_aer_err_z'],
            'subaer_comp_uncertainties': [
                'x_subaer_a', 
                'x_subaer_b', 
                'x_subaer_r', 
                'x_subaer_p', 
                'x_subaer_h', 
                'x_subaer_x', 
                'x_subaer_y', 
                'x_subaer_z', 
                'x_subaer_rho', 
                'y_subaer_a', 
                'y_subaer_b', 
                'y_subaer_r', 
                'y_subaer_p', 
                'y_subaer_h', 
                'y_subaer_x', 
                'y_subaer_y', 
                'y_subaer_z', 
                'y_subaer_rho', 
                'z_subaer_a', 
                'z_subaer_b', 
                'z_subaer_r', 
                'z_subaer_p', 
                'z_subaer_h', 
                'z_subaer_x', 
                'z_subaer_y', 
                'z_subaer_z', 
                'z_subaer_rho'],
            'tpu_data': [
                'subaerial_thu', 
                'subaerial_tvu', 
                'subaqueous_thu', 
                'subaqueous_tvu', 
                'total_thu', 
                'total_tvu']
            }

        for k, v in diag_data_fields.items():
            data = {}
            for field in v:
                print(f'adding {field} data to array...')
                data[field] = []
                for fl_df in diag_dfs:
                    data[field].extend(fl_df[field].to_list())
            
            df = pd.DataFrame(data)
            out_path = Path(self.tpu_output) / f'{las_base_name}_{k}.pkl'
            print(f'pickling {out_path}...')
            df.to_pickle(str(out_path))

    def output_diagnostic_data(self, las_short_name, fl, merged_data, 
                               stddev, subaer_obj, subaqu_obj, 
                               total_thu, total_tvu, raw_class):

        print(f'outputting diagnostic data - {las_short_name}, flight line {fl}...')

        las_pos_xyz = (merged_data[2], merged_data[3], merged_data[4], )
        sensor_model_diag_data = subaer_obj.jacobian.sensor_model.get_sensor_model_diagnostic_data(las_pos_xyz)

        diag_data = {
            'las_name': las_short_name,
            'flight_line': fl,
            'raw_class': raw_class,
            'las_t': merged_data[1],
            'las_x': merged_data[2],
            'las_y': merged_data[3],
            'las_z': merged_data[4],
            'sbet_t': merged_data[0],
            'sbet_x': merged_data[5],
            'sbet_y': merged_data[6],
            'sbet_z': merged_data[7],
            'r': merged_data[8],
            'p': merged_data[9],
            'h': merged_data[10],
            'std_a': stddev[0],
            'std_b': stddev[1],
            'std_r': stddev[2],
            'std_p': stddev[3],
            'std_h': stddev[4],
            'stdx_sbet': stddev[5],
            'stdy_sbet': stddev[6],
            'stdz_sbet': stddev[7],
            'std_rho': stddev[8],
            'rho_est': sensor_model_diag_data[0],
            'a_est': sensor_model_diag_data[1],
            'b_est': sensor_model_diag_data[2],
            'aer_x_pre_poly': sensor_model_diag_data[3],
            'aer_y_pre_poly': sensor_model_diag_data[4],
            'aer_z_pre_poly': sensor_model_diag_data[5],
            'dx': sensor_model_diag_data[6],
            'dy': sensor_model_diag_data[7],
            'dz': sensor_model_diag_data[8],
            'cblue_aer_x': sensor_model_diag_data[9],  # np.round_(total_thu * 100).astype('int')
            'cblue_aer_y': sensor_model_diag_data[10],
            'cblue_aer_z': sensor_model_diag_data[11],
            'cblue_aer_err_x': sensor_model_diag_data[12],
            'cblue_aer_err_y': sensor_model_diag_data[13],
            'cblue_aer_err_z': sensor_model_diag_data[14],
            'x_subaer_a': np.round_(subaer_obj.x_comp_uncertainties[0] * 1000).astype('uint16'),
            'x_subaer_b': np.round_(subaer_obj.x_comp_uncertainties[1] * 1000).astype('uint16'),
            'x_subaer_r': np.round_(subaer_obj.x_comp_uncertainties[2] * 1000).astype('uint16'),
            'x_subaer_p': np.round_(subaer_obj.x_comp_uncertainties[3] * 1000).astype('uint16'),
            'x_subaer_h': np.round_(subaer_obj.x_comp_uncertainties[4] * 1000).astype('uint16'),
            'x_subaer_x': np.round_(subaer_obj.x_comp_uncertainties[5] * 1000).astype('uint16'),
            'x_subaer_y': None,
            'x_subaer_z': None,
            'x_subaer_rho': np.round_(subaer_obj.x_comp_uncertainties[6] * 1000).astype('uint16'),
            'y_subaer_a': np.round_(subaer_obj.y_comp_uncertainties[0] * 1000).astype('uint16'),
            'y_subaer_b': np.round_(subaer_obj.y_comp_uncertainties[1] * 1000).astype('uint16'),
            'y_subaer_r': np.round_(subaer_obj.y_comp_uncertainties[2] * 1000).astype('uint16'),
            'y_subaer_p': np.round_(subaer_obj.y_comp_uncertainties[3] * 1000).astype('uint16'),
            'y_subaer_h': np.round_(subaer_obj.y_comp_uncertainties[4] * 1000).astype('uint16'),
            'y_subaer_x': None,
            'y_subaer_y': np.round_(subaer_obj.y_comp_uncertainties[5] * 1000).astype('uint16'),
            'y_subaer_z': None,
            'y_subaer_rho': np.round_(subaer_obj.y_comp_uncertainties[6] * 1000).astype('uint16'),
            'z_subaer_a': np.round_(subaer_obj.z_comp_uncertainties[0] * 1000).astype('uint16'),
            'z_subaer_b': np.round_(subaer_obj.z_comp_uncertainties[1] * 1000).astype('uint16'),
            'z_subaer_r': np.round_(subaer_obj.z_comp_uncertainties[2] * 1000).astype('uint16'),
            'z_subaer_p': np.round_(subaer_obj.z_comp_uncertainties[3] * 1000).astype('uint16'),
            'z_subaer_h': None,
            'z_subaer_x': None,
            'z_subaer_y': None,
            'z_subaer_z': np.round_(subaer_obj.z_comp_uncertainties[4] * 1000).astype('uint16'),
            'z_subaer_rho': np.round_(subaer_obj.z_comp_uncertainties[5] * 1000).astype('uint16'),
            'subaerial_thu': subaer_obj.thu,
            'subaerial_tvu': subaer_obj.tvu,
            'subaqueous_thu': subaqu_obj.thu,
            'subaqueous_tvu': subaqu_obj.tvu,
            'total_thu': total_thu,
            'total_tvu': total_tvu,
            }

        return pd.DataFrame(diag_data)

    def calc_tpu(self, sbet_las_files):
        """

        :param sbet_las_tile: generator yielding sbet data and las tile name for each las tile
        :return:
        """

        sbet, las_file, jacobian, merge = sbet_las_files

        data_to_output = []

        # CREATE LAS OBJECT TO ACCESS INFORMATION IN LAS FILE
        las = Las(las_file)
        
        diag_dfs = []

        if las.num_file_points:  # i.e., if las had data points
            logging.info('{} ({:,} points)'.format(las.las_short_name, las.num_file_points))
            logging.debug('flight lines {}'.format(las.unq_flight_lines))
            unsorted_las_xyzt, t_argsort, flight_lines = las.get_flight_line_txyz()

            self.flight_line_stats = {}  # reset flight line stats dict
            for fl in las.unq_flight_lines:

                logging.debug('flight line {} {}'.format(fl, '-' * 50))

                # las_xyzt has the same order as points in las (i.e., unordered)
                fl_idx = flight_lines == fl
                fl_unsorted_las_xyzt = unsorted_las_xyzt[fl_idx]
                fl_t_argsort = t_argsort[fl_idx]
                fl_las_idx = t_argsort.argsort()[fl_idx]

                num_fl_points = np.sum(fl_idx)  # count Trues
                logging.debug(f'{las.las_short_name} fl {fl}: {num_fl_points} points')

                # CREATE MERGED-DATA OBJECT M
                logging.debug('({}) merging trajectory and las data...'.format(las.las_short_name))
                merged_data, stddev, unsort_idx, raw_class = merge.merge(las.las_short_name, fl, sbet.values,
                                                                   fl_unsorted_las_xyzt, fl_t_argsort, fl_las_idx)

                if merged_data is not False:  # i.e., las and sbet is merged

                    logging.debug('({}) calculating subaer thu/tvu...'.format(las.las_short_name))
                    subaer_obj = Subaerial(jacobian, merged_data, stddev)
                    subaer_thu, subaer_tvu = subaer_obj.calc_subaerial_tpu()
                    depth = merged_data[4] - self.water_surface_ellipsoid_height

                    logging.debug('({}) calculating subaqueous thu/tvu...'.format(las.las_short_name))
                    subaqu_obj = Subaqueous(self.surface_ind, self.wind_val, 
                                            self.kd_val, depth, self.subaqueous_luts)
                    subaqu_thu, subaqu_tvu = subaqu_obj.fit_lut()
                    self.subaqu_lookup_params = subaqu_obj.get_subaqueous_meta_data()
                    vdatum_mcu = float(self.vdatum_region_mcu) / 100.0  # file is in cm (1-sigma)

                    logging.debug('({}) calculating total thu...'.format(las.las_short_name))
                    total_thu = ne.evaluate('sqrt(subaer_thu**2 + subaqu_thu**2)')

                    logging.debug('({}) calculating total tvu...'.format(las.las_short_name))
                    total_tvu = ne.evaluate('sqrt(subaer_tvu**2 + subaqu_tvu**2 + vdatum_mcu**2)')

                    fl_tpu_data = np.vstack((
                        #np.round_(total_thu * 1000).astype('uint16'),
                        #np.round_(total_tvu * 1000).astype('uint16'),
                        total_thu,
                        total_tvu,
                        merged_data[1],
                        merged_data[2],
                        merged_data[3],
                        merged_data[4],
                        raw_class,
                        unsort_idx
                        )).T

                    print(fl_tpu_data)
                    data_to_output.append(fl_tpu_data)

                    self.update_fl_stats(fl, num_fl_points, fl_tpu_data)

                    #diag_dfs.append(self.output_diagnostic_data(las.las_short_name, fl,
                    #                                            merged_data, stddev, 
                    #                                            subaer_obj, subaqu_obj, 
                    #                                            total_thu, total_tvu, raw_class))

                else:
                    logging.warning('SBET and LAS not merged because max delta '
                                    'time exceeded acceptable threshold of {} '
                                    'sec(s).'.format(merge.max_allowable_dt))

                    self.flight_line_stats.update(
                        {'{} (0/{} points with TPU)'.format(fl, num_fl_points): None})

            self.write_metadata(las)  # TODO: include as VLR?
            self.output_tpu_to_las_extra_bytes(las, data_to_output)

            ## merge fl diagnostic dataframes
            #self.export_diag_data(las.las_base_name, diag_dfs)

        else:
            logging.warning('WARNING: {} has no data points'.format(las.las_short_name))

    def output_tpu_to_las_extra_bytes(self, las, data_to_output):
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

            total_thu,  unsigned short (2 bytes), total horizontal uncertainty
            total_tvu,  unsigned short (2 bytes), total vertical uncertainty

        :param las:
        :param data_to_output:
        :param output_columns:
        :return:
        """

        out_las_name = os.path.join(self.tpu_output, las.las_base_name) + '_TPU.las'
        logging.debug('logging las and tpu results to {}'.format(out_las_name))
        in_las = laspy.file.File(las.las, mode="r")  # las is Las object
        out_las = laspy.file.File(out_las_name, mode="w", header=in_las.header)

        tpu_data_type = 9  # 3 = laspy unsigned short (2 bytes)

        extra_byte_dimensions = OrderedDict([
            ('total_thu', tpu_data_type),
            ('total_tvu', tpu_data_type),
            ('t', tpu_data_type),
            ('x', tpu_data_type),
            ('y', tpu_data_type),
            ('z', tpu_data_type),
            ('raw_class', tpu_data_type),
            ('unsort_idx', tpu_data_type)
            ])

        num_extra_bytes = len(extra_byte_dimensions.keys())

        # define new extrabyte dimensions
        for dimension, dtype in extra_byte_dimensions.items():
            logging.debug('creating extra byte dimension for {}...'.format(dimension))
            out_las.define_new_dimension(name=dimension, 
                                         data_type=dtype,
                                         description=dimension)

        if len(data_to_output) != 0:
            tpu_data = np.vstack(data_to_output)
            print(tpu_data)
            extra_byte_df = pd.DataFrame(tpu_data, 
                                         index=tpu_data[:, -1], 
                                         columns=extra_byte_dimensions.keys())
            print(extra_byte_df)
                
            if extra_byte_df.shape[0] == las.num_file_points:
                extra_byte_df = extra_byte_df.sort_index()
            else:
                '''fill data points for which TPU was not calculated 
                with no_data_value (also sorts by index, or t_idx)'''
                no_data_value = -1
                extra_byte_df = extra_byte_df.reindex(las.t_argsort, 
                                                      fill_value=no_data_value)

            logging.debug('populating extra byte data for total_thu...')
            out_las.total_thu = extra_byte_df['total_thu']
        
            logging.debug('populating extra byte data for total_tvu...')
            out_las.total_tvu = extra_byte_df['total_tvu']
            
            logging.debug('populating extra byte data for t...')
            out_las.t = extra_byte_df['t']
        
            logging.debug('populating extra byte data for x...')
            out_las.x = extra_byte_df['x']

            logging.debug('populating extra byte data for y...')
            out_las.y = extra_byte_df['y']
        
            logging.debug('populating extra byte data for z...')
            out_las.z = extra_byte_df['z']

            logging.debug('populating extra byte data for raw_class...')
            out_las.raw_class = extra_byte_df['raw_class']

            logging.debug('populating extra byte data for unsort_idx...')
            out_las.unsort_idx = extra_byte_df['unsort_idx']

            #logging.debug('populating extra byte data for masked_fl_t_idx...')
            #out_las.masked_fl_t_idx = extra_byte_df['masked_fl_t_idx']
        else:
            logging.debug('populating extra byte data for total_thu...')
            out_las.total_thu = np.zeros(las.num_file_points)
        
            logging.debug('populating extra byte data for total_tvu...')
            out_las.total_tvu = np.zeros(las.num_file_points)

        # copy data from in_las
        for field in in_las.point_format:
            logging.debug('writing {} to {} ...'.format(field.name, out_las))
            las_data = in_las.reader.get_dimension(field.name)
            out_las.writer.set_dimension(field.name, las_data[las.t_argsort])

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

        logging.debug('({}) creating TPU meta data file...'.format(las.las_short_name))
        self.metadata.update({
            'subaqueous lookup params': self.subaqu_lookup_params,
            'water surface': self.surface_select,
            'wind': self.wind_selection,
            'kd': self.kd_selection,
            'VDatum region': self.vdatum_region,
            'VDatum region MCU': self.vdatum_region_mcu,
            'flight line stats (min max mean stddev)': self.flight_line_stats,
            'sensor model': self.sensor_model,
            'cBLUE version': self.cblue_version,
            'cpu_processing_info': self.cpu_process_info, 
            'water_surface_ellipsoid_height': self.water_surface_ellipsoid_height,
        })

        try:
            #self.metadata['flight line stats'].update(self.flight_line_stats)  # flight line metadata
            with open(os.path.join(self.tpu_output, '{}.json'.format(las.las_base_name)), 'w') as outfile:
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

        print('Calculating TPU (multi-processing)...')
        p = pp.ProcessPool(4)

        for _ in tqdm(p.imap(self.calc_tpu, sbet_las_generator), total=num_las, ascii=True):
            pass

        return p


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

        print('Calculating TPU (single-processing)...')
        with progressbar.ProgressBar(max_value=num_las) as bar:
            for i, sbet_las in enumerate(sbet_las_generator):
                bar.update(i)
                self.calc_tpu(sbet_las)


if __name__ == '__main__':
    pass
