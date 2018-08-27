import logging
logging.basicConfig(format='%(asctime)s:%(message)s', level=logging.INFO)
import numpy as np
import numexpr as ne
import pandas as pd

from Sbet import Sbet
from Las import Las
from Merge import Merge
from Subaerial import Subaerial
from Subaqueous import Subaqueous
from Datum import Datum

import pathos.pools as pp  # for multiprocessing of las files

from lxml import etree


class Tpu:

    def __init__(self, surface_select,
                 surface_ind, wind_selection, wind_val,
                 kd_selection, kd_val, vdatum_region,
                 vdatum_region_mcu, tpu_output, fR, fJ1, fJ2, fJ3, fF):
        self.surface_select = surface_select
        self.surface_ind = surface_ind
        self.wind_selection = wind_selection
        self.wind_val = wind_val
        self.kdSelect = kd_selection
        self.kd_val = kd_val
        self.vdatum_region = vdatum_region
        self.vdatum_region_mcu = vdatum_region_mcu
        self.tpuOutput = tpu_output
        self.fR = fR
        self.fJ1 = fJ1
        self.fJ2 = fJ2
        self.fJ3 = fJ3
        self.fF = fF

    def calc_tpu(self, las, sbet):
        las = Las(las)
        logging.info('{}\n{}'.format('#' * 30, las.las_short_name))
        las.set_bathy_points()
        data_to_pickle = []

        logging.info(las.get_flight_line_ids())
        for fl in las.get_flight_line_ids():
            logging.info('flight line {} {}'.format(fl, '-' * 30))
            D = Merge.merge(las.las_short_name, fl, sbet.values, las.get_flight_line_txyz(fl))

            logging.info('({}) calculating subaerial TPU...'.format(las.las_short_name))
            subaerial = Subaerial(D, self.fR).calc_subaerial(self.fJ1, self.fJ2, self.fJ3, self.fF)
            depth = subaerial[:, 2] + 23

            logging.info('({}) calculating subaqueous TPU...'.format(las.las_short_name))
            subaqueous = Subaqueous.main(self.surface_ind, self.wind_val, self.kd_val, depth)

            logging.info('({}) calculating datum TPU...'.format(las.las_short_name))
            # datum = Datum()
            vdatum_mcu = float(self.vdatum_region_mcu) / 100.0  # file is in cm (1-sigma)

            logging.info('({}) calculating total TPU...'.format(las.las_short_name))
            subaerial_sig_xyz = subaerial[:, 6]
            sigma = ne.evaluate('sqrt(subaqueous**2 + subaerial_sig_xyz**2 + vdatum_mcu**2)')

            num_points = sigma.shape[0]
            output = np.hstack((
                np.round_(subaerial, decimals=5),
                np.round_(np.expand_dims(subaqueous, axis=1), decimals=5),
                np.round_(np.expand_dims(sigma, axis=1), decimals=5),
                np.full((num_points, 1), fl)))

            data_to_pickle.append(output)

        # write data to file
        output_tpu_file = r'{}_TPU.tpu'.format(las.las_short_name.replace('.las', ''))
        output_path = '{}\\{}'.format(self.tpuOutput, output_tpu_file)
        output_df = pd.DataFrame(np.vstack(data_to_pickle))
        logging.info('({}) writing TPU...'.format(las.las_short_name))
        output_df.to_pickle(output_path)

    def __str__(self):
        meta_data = {
            'water surface', self.surface_select,
            'wind', self.wind_selection,
            'kd', self.kdSelect,
            'VDatum region', self.vdatum_region,
            'VDatum region MCU', self.vdatum_region_mcu,
        }

        meta_dat_json = json.dumps(meta_data)
        return meta_data_json


    def create_metadata(self, las):
        logging.info('({}) creating TPU meta data file...'.format(las.las_short_name))




    def run_tpu(self, las, sbet):
        self.calc_tpu(las, sbet)
        self.create_metadata(las)

    def run_tpu_multiprocessing(self, las_files, sbet_files):

        p = pp.ProcessPool()
        p.imap(self.run_tpu, las_files, sbet_files)
        p.close()
        p.join()


if __name__ == '__main__':
    pass
