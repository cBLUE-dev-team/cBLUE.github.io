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

Last Edited By:
Keana Kief (OSU)
May 17th, 2024

"""

import logging
from pathos import logger
import pathos.pools as pp
import json
import os
import laspy
import numpy as np
import pandas as pd
import progressbar
from tqdm import tqdm
from Subaerial import Subaerial
from Subaqueous import Subaqueous
from Las import Las

logger = logging.getLogger(__name__)


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

    def __init__(self, gui_object, sensor_object):

        #Store the gui_object information
        self.gui_object = gui_object
        #Store the sensor_obejct information          
        self.sensor_object = sensor_object

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
            "total_thu": 0,
            "total_tvu": 1,
        }

        fl_stats_strs = []
        for fl_stat, ind in fl_stat_indx.items():

            fl_stats_vals = (
                fl_stat,
                fl_tpu_min[ind],
                fl_tpu_max[ind],
                fl_tpu_mean[ind],
                fl_tpu_stddev[ind],
            )

            fl_stats_str = "{}: {:6.3f}{:6.3f}{:6.3f}{:6.3f}".format(*fl_stats_vals)
            fl_stats_strs.append(fl_stats_str)

        fl_header_str = f"{fl} ({fl_tpu_count}/{num_fl_points} points with TPU)"
        self.flight_line_stats.update({fl_header_str: fl_stats_strs})

    def calc_tpu(self, sbet_las_files):
        """

        :param sbet_las_tile: generator yielding sbet data and las tile name for each las tile
        :return:
        """

        sbet, las_file, jacobian, merge = sbet_las_files

        data_to_output = []

        # CREATE LAS OBJECT TO ACCESS INFORMATION IN LAS FILE
        las = Las(las_file)

        if las.num_file_points:  # i.e., if las had data points
            logger.tpu(
                "{} ({:,} points)".format(las.las_short_name, las.num_file_points)
            )
            logger.tpu("flight lines {}".format(las.unq_flight_lines))

            unsorted_las_xyztcf, t_argsort, flight_lines = las.get_flight_line(self.sensor_object.type)

            self.flight_line_stats = {}  # reset flight line stats dict
            for fl in las.unq_flight_lines:

                logger.tpu("flight line {} \n{}\n".format(fl, "-" * 50))

                # las_xyzt has the same order as points in las (i.e., unordered)
                fl_idx = flight_lines == fl
                fl_unsorted_las_xyztcf = unsorted_las_xyztcf[fl_idx]
                fl_t_argsort = t_argsort[fl_idx]
                fl_las_idx = t_argsort.argsort()[fl_idx]

                num_fl_points = np.sum(fl_idx)  # count Trues
                logger.tpu(f"{las.las_short_name} fl {fl}: {num_fl_points} points")

                # CREATE MERGED-DATA OBJECT

                logger.tpu(
                    "({}) merging trajectory and las data...".format(las.las_short_name)
                )

                merged_data, stddev, unsort_idx, raw_class, masked_fan_angle = merge.merge(
                    las,
                    fl,
                    sbet.values,
                    fl_unsorted_las_xyztcf,
                    fl_t_argsort,
                    fl_las_idx,
                    self.sensor_object,
                )

                if merged_data is not False:  # i.e., las and sbet is merged

                    logger.tpu(
                        "({}) calculating subaer thu/tvu...".format(las.las_short_name)
                    )
                    subaer_obj = Subaerial(jacobian, merged_data, stddev)

                    subaer_thu, subaer_tvu = subaer_obj.calc_subaerial_tpu()

                    depth = self.gui_object.water_surface_ellipsoid_height - merged_data[4]

                    # print(f"\nMax depth: {max(depth)}")
                    # print(f"Min depth: {min(depth)}")

                    logger.tpu(
                        "({}) calculating subaqueous thu/tvu...".format(
                            las.las_short_name
                        )
                    )

                    #Initalize the subaqueous object
                    subaqu_obj = Subaqueous(
                        self.gui_object,
                        depth,
                        self.sensor_object,
                        raw_class
                    )

                    if(self.sensor_object.type == "multi"):
                        #Multi beam sensor: Sending to multi_beam_fit_lut() 
                        subaqu_thu, subaqu_tvu = subaqu_obj.multi_beam_fit_lut(masked_fan_angle) 
                    
                    else:
                        #Single beam Sensor: Sending to fit_lut() 
                        subaqu_thu, subaqu_tvu = subaqu_obj.fit_lut()     

                    vdatum_mcu = (
                        float(self.gui_object.mcu) / 100.0
                    )  # file is in cm (1-sigma)

                    logger.tpu(
                        "({}) calculating total thu...".format(las.las_short_name)
                    )

                    # sum in quadrature - get 95% confidence level
                    total_thu = np.sqrt(subaer_thu**2 + subaqu_thu**2)

                    logger.tpu(
                        "({}) calculating total tvu...".format(las.las_short_name)
                    )

                    # sum in quadrature - get 95% confidence level
                    total_tvu = np.sqrt(
                        subaer_tvu**2 + subaqu_tvu**2 + vdatum_mcu**2
                    )

                    # convert to 95% conf, if requested
                    if self.gui_object.error_type == "95% confidence":
                        logging.tpu("TPU reported at 95% confidence...")
                        total_thu *= 1.7308
                        total_tvu *= 1.96
                    else:
                        logging.tpu("TPU reported at 1 sigma...")

                    # print(f"{total_tvu[2279775]}")

                    fl_tpu_data = np.vstack((total_thu, total_tvu, unsort_idx)).T

                    data_to_output.append(fl_tpu_data)

                    self.update_fl_stats(fl, num_fl_points, fl_tpu_data)

                else:
                    logger.warning(
                        "SBET and LAS not merged because max delta "
                        "time exceeded acceptable threshold of {} "
                        "sec(s).".format(merge.max_allowable_dt)
                    )

                    self.flight_line_stats.update(
                        {"{} (0/{} points with TPU)".format(fl, num_fl_points): None}
                    )

            self.write_metadata(las)  # TODO: include as VLR?

            try:
                self.output_tpu_to_las_extra_bytes(las, data_to_output)
            except ValueError as e:
                raise ValueError("Las files already contain thu and tvu")

        else:
            logger.warning("WARNING: {} has no data points".format(las.las_short_name))

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

        # Get input file name and append _TPU and file extension.
        # If the user has selected .laz ouput, append .laz
        if self.gui_object.laz_option:
            out_laz_name = os.path.join(self.gui_object.output_directory, las.las_base_name) + "_TPU.laz"
            
            # if TPU file already exists, notify the user that it will be overwritten
            if os.path.exists(out_laz_name):
                # Remove the old file
                os.remove(out_laz_name)
                logger.tpu(
                    "writing laz and tpu results to existing file: {}".format(out_laz_name)
                )
            # otherwise, create new TPU file
            else:
                logger.tpu(
                    "writing laz and tpu results to new file: {}".format(out_laz_name)
                )

        # If the user has selected .las ouput, append .las
        if self.gui_object.las_option:
            out_las_name = os.path.join(self.gui_object.output_directory, las.las_base_name) + "_TPU.las"

            # if TPU file already exists, notify the user that it will be overwritten
            if os.path.exists(out_las_name):
                # Remove the old file
                os.remove(out_las_name)
                logger.tpu(
                    "writing las and tpu results to existing file: {}".format(out_las_name)
                )
            # otherwise, create new TPU file
            else:
                logger.tpu(
                    "writing las and tpu results to new file: {}".format(out_las_name)
                )

        # read las file
        in_las = laspy.read(las.las)
        # print(in_las.header)
        # print(in_las.vlrs)

        # note '<f4' -> 32 bit floating point
        # extra_byte_dimensions = {"total_thu": "<f4", "total_tvu": "<f4"}
        extra_byte_dimensions = [laspy.ExtraBytesParams(name="total_thu", type="<f4", description="total_thu"), \
                                 laspy.ExtraBytesParams(name="total_tvu", type="<f4", description="total_tvu")]

        num_extra_bytes = len(extra_byte_dimensions)

        # define new extrabyte dimensions
        # for dimension, dtype in extra_byte_dimensions.items():

        logger.tpu("creating extra byte dimension for total_thu and total_tvu")
        in_las.add_extra_dims(extra_byte_dimensions)
        # print(in_las.header)
        # print(in_las.vlrs)

        if len(data_to_output) != 0:
            tpu_data = np.vstack(data_to_output)
            extra_byte_df = pd.DataFrame(
                tpu_data[:, 0:num_extra_bytes],
                index=tpu_data[:, num_extra_bytes],
                columns=["total_thu", "total_tvu"],
            )
            # print(f"extra_byte_dims: {extra_byte_dimensions}")
            # print(f"extra_byte_df: {extra_byte_df}")

            if extra_byte_df.shape[0] == las.num_file_points:
                extra_byte_df = extra_byte_df.sort_index()
                # print(f"extra_byte_df\n-------------")
                # print(extra_byte_df)

            else:

                logger.tpu(
                    """
                filling data points for which TPU was not calculated
                with no_data_value (also sorting by index, or t_idx)
                """
                )
                no_data_value = -1

                extra_byte_df = extra_byte_df.reindex(
                    las.t_argsort, fill_value=no_data_value
                ).sort_index()

            logger.tpu("populating extra byte data for total_thu...")
            in_las.total_thu = extra_byte_df["total_thu"]
            # print(f"THU: {in_las.total_thu}")


            logger.tpu("populating extra byte data for total_tvu...")
            in_las.total_tvu = extra_byte_df["total_tvu"]
            # print(f"TVU: {in_las.total_tvu}")



        else:
            logger.tpu("populating extra byte data for total_thu...")
            in_las.total_thu = np.zeros(las.num_file_points)
            logger.tpu("populating extra byte data for total_tvu...")
            in_las.total_tvu = np.zeros(las.num_file_points)

        # If the user has selected .laz ouput, append .laz
        if self.gui_object.laz_option:
            in_las.write(out_laz_name)
        # If the user has selected .las ouput, append .las
        if self.gui_object.las_option:
            in_las.write(out_las_name)

        # print("Wrote in_las")

        # for field in in_las.point_format:
        #     print({field.name})

        if self.gui_object.csv_option:
            logger.tpu(f"Saving CSV as {las.las_base_name}_TPU.csv")

            # get name of csv from las file
            out_csv_name = os.path.join(self.gui_object.output_directory, las.las_base_name) + "_TPU.csv"

            # print(f"out_csv_name{out_csv_name}")
            # print(f"out_las_name{out_las_name}")

            # try:
            #     csv_las = Las(out_las_name)
            # except ValueError as e:
            #     raise ValueError(f"Error: {e}, Laspy failed to read {out_las_name}")

            #xyz_to_coordinate converts the x, y, z integer values to decimal values
            x, y, z = las.xyz_to_coordinate()

            try:
                # Save relevant data to csv
                pd.DataFrame.from_dict(
                    {
                        "GPS Time": in_las.gps_time,
                        "X": x,
                        "Y": y,
                        "Z": z,
                        "THU": in_las.total_thu,
                        "TVU": in_las.total_tvu,
                        "Classification": in_las.classification,
                    }
                ).to_csv(out_csv_name, index=False)
            except ValueError as e:
                raise ValueError("CSV writing failed")

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

        logger.tpu("({}) creating TPU meta data file...".format(las.las_short_name))
        self.metadata.update(
            {
                "subaqueous lookup params": self.subaqu_lookup_params,
                "wind": self.gui_object.wind_selection,
                "kd": self.gui_object.kd_selection,
                "VDatum region": self.gui_object.vdatum_region,
                "VDatum region MCU": self.gui_object.mcu,
                "flight line stats (min max mean stddev)": self.flight_line_stats,
                "sensor model": self.sensor_object.name,
                "cBLUE version": self.gui_object.cblue_version,
                "Subaqueous processing version": self.gui_object.subaqueous_version,
                "cpu_processing_info": self.gui_object.cpu_process_info,
                "water_surface_ellipsoid_height": self.gui_object.water_surface_ellipsoid_height,
                "Error type": self.gui_object.error_type
            }
        )

        try:
            # self.metadata['flight line stats'].update(self.flight_line_stats)  # flight line metadata
            with open(
                os.path.join(self.gui_object.output_directory, "{}.json".format(las.las_base_name)), "w", encoding="utf-8"
            ) as outfile:

                json.dump(self.metadata, outfile, indent=1, ensure_ascii=False)
        except Exception as e:
            logger.error(e)
            print(e)

    def run_tpu_multiprocess(self, num_las, sbet_las_generator):
        """runs the tpu calculations using multiprocessing

        This methods initiates the tpu calculations using the pathos
        multiprocessing framework (https://pypi.org/project/pathos/).
        Whether the tpu calculations are done with multiprocessing or not is
        currently determined by which "run_tpu_*" method is manually specified
        in the tpu_process_callback() method of the CBlueApp class.

        TODO: Include user option to select single processing or multiprocessing

        :param sbet_las_generator:
        :return:
        """

        print("Calculating TPU (multi-processing)...")
        p = pp.ProcessPool(2)

        for _ in tqdm(
            p.imap(self.calc_tpu, sbet_las_generator), total=num_las, ascii=True
        ):
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

        print("Calculating TPU (single-processing)...")
        with progressbar.ProgressBar(max_value=num_las) as bar:
            for i, sbet_las in enumerate(sbet_las_generator):
                bar.update(i)
                self.calc_tpu(sbet_las)


if __name__ == "__main__":
    pass
