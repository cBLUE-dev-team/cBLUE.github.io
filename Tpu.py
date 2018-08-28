import logging
logging.basicConfig(format='%(asctime)s:%(message)s', level=logging.INFO)
import pathos.pools as pp
import json
import os
import numpy as np
import numexpr as ne
import pandas as pd

from Las import Las
from Merge import Merge
from Subaerial import Subaerial
from Subaqueous import Subaqueous


class Tpu:

    def __init__(self, subaqueous_metadata, surface_select,
                 surface_ind, wind_selection, wind_val,
                 kd_selection, kd_val, vdatum_region,
                 vdatum_region_mcu, tpu_output, fR, fJ1, fJ2, fJ3, fF):
        self.subaqueous_lookup_params = subaqueous_metadata
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
        self.metadata = {}
        self.flight_line_stats = {}

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
            subaerial, subaerial_columns = Subaerial(D, self.fR).calc_subaerial(self.fJ1, self.fJ2, self.fJ3, self.fF)
            depth = subaerial[:, 2] + 23

            logging.info('({}) calculating subaqueous TPU...'.format(las.las_short_name))
            subaqueous_sz, subaqueous_columns = Subaqueous.main(self.surface_ind, self.wind_val, self.kd_val, depth)

            logging.info('({}) calculating datum TPU...'.format(las.las_short_name))
            vdatum_mcu = float(self.vdatum_region_mcu) / 100.0  # file is in cm (1-sigma)

            logging.info('({}) calculating total TPU...'.format(las.las_short_name))
            subaerial_sz = subaerial[:, 5]
            total_sz = ne.evaluate('sqrt(subaqueous_sz**2 + subaerial_sz**2 + vdatum_mcu**2)')

            num_points = total_sz.shape[0]
            output = np.hstack((
                np.round_(subaerial, decimals=5),
                np.round_(np.expand_dims(subaqueous_sz, axis=1), decimals=5),
                np.round_(np.expand_dims(total_sz, axis=1), decimals=5)))

            sigma_columns = ['total_sz']
            output_columns = subaerial_columns + subaqueous_columns + sigma_columns
            data_to_pickle.append(output)
            stats = ['min', 'max', 'mean', 'std']
            self.flight_line_stats[str(fl)] = pd.DataFrame(output, columns=output_columns).describe().loc[stats].to_dict()

        # write data to file
        output_tpu_file = r'{}_TPU.tpu'.format(las.las_base_name)
        output_path = '{}\\{}'.format(self.tpuOutput, output_tpu_file)
        output_df = pd.DataFrame(np.vstack(data_to_pickle))
        logging.info('({}) writing TPU...'.format(las.las_short_name))
        output_df.to_pickle(output_path)

        # write metadata to json file
        self.write_metadata(las)

    def write_metadata(self, las):
        logging.info('({}) creating TPU meta data file...'.format(las.las_short_name))
        self.metadata.update({
            'subaqueous lookup params': self.subaqueous_lookup_params,
            'water surface': self.surface_select,
            'wind': self.wind_selection,
            'kd': self.kdSelect,
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

    def run_tpu_multiprocessing(self, las_files, sbet_files):
        p = pp.ProcessPool()
        p.imap(self.calc_tpu, las_files, sbet_files)
        p.close()
        p.join()


if __name__ == '__main__':
    pass
