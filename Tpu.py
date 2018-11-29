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
from Subaqueous_frt import Subaqueous


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
        """
        Summary line.

        Extended description of function.

        Parameters
        ----------
        arg1 : int
            Description of arg1
        arg2 : str
            Description of arg2

        Returns
        -------
        int
            Description of return value

        """

        las = Las(las)
        logging.info('{}\n{}'.format('#' * 30, las.las_short_name))
        data_to_pickle = []

        logging.info(las.get_flight_line_ids())
        for fl in las.get_flight_line_ids():
            logging.info('flight line {} {}'.format(fl, '-' * 30))
            D = Merge.merge(las.las_short_name, fl, sbet.values, las.get_flight_line_txyz(fl))

            logging.info('({}) calculating subaerial THU/TVU...'.format(las.las_short_name))
            subaerial, subaerial_columns = Subaerial(D, self.fR).calc_subaerial(
                self.fJ1, self.fJ2, self.fJ3, self.fF)
            depth = subaerial[:, 2] + las.get_average_depth()
            subaerial_thu = subaerial[:, 3]
            subaerial_tvu = subaerial[:, 4]

            logging.info('({}) calculating subaqueous THU/TVU...'.format(las.las_short_name))
            subaqueous_thu, subaqueous_tvu, subaqueous_columns = Subaqueous.main(
                self.surface_ind, self.wind_val, self.kd_val, depth)

            vdatum_mcu = float(self.vdatum_region_mcu) / 100.0  # file is in cm (1-sigma)

            logging.info('({}) calculating total THU...'.format(las.las_short_name))
            total_thu = ne.evaluate('sqrt(subaerial_thu**2 + subaqueous_thu**2)')

            logging.info('({}) calculating total TVU...'.format(las.las_short_name))
            total_tvu = ne.evaluate('sqrt(subaqueous_tvu**2 + subaerial_tvu**2 + vdatum_mcu**2)')

            num_points = total_tvu.shape[0]
            output = np.hstack((
                np.round_(subaerial, decimals=5),
                np.round_(np.expand_dims(subaqueous_thu, axis=1), decimals=5),
                np.round_(np.expand_dims(subaqueous_tvu, axis=1), decimals=5),
                np.round_(np.expand_dims(total_thu, axis=1), decimals=5),
                np.round_(np.expand_dims(total_tvu, axis=1), decimals=5)))

            sigma_columns = ['total_thu', 'total_tvu']
            output_columns = subaerial_columns + subaqueous_columns + sigma_columns  # TODO: doesn't need to happen every iteration
            data_to_pickle.append(output)
            stats = ['min', 'max', 'mean', 'std']
            self.flight_line_stats[str(fl)] = pd.DataFrame(
                output, columns=output_columns).describe().loc[stats].to_dict()

        pickle_tpu(data_to_pickle, output_columns)  # current output
        #output_new_las_with_tpu_xbytes()  # want to move to this?
        out
        self.write_metadata(las)

    def pickle_tpu(self, data_to_pickle, output_columns):
        output_tpu_file = r'{}_TPU.tpu'.format(las.las_base_name)
        output_path = '{}\\{}'.format(self.tpuOutput, output_tpu_file)
        output_df = pd.DataFrame(np.vstack(data_to_pickle), columns=output_columns)
        logging.info('({}) writing TPU...'.format(las.las_short_name))
        output_df.to_pickle(output_path)

    def output_new_las_with_tpu_xbytes(self, las):
        inFile = laspy.file.File(las, mode = "r")
        outFile = laspy.file.File("./laspytest/data/output.las", mode = "w",
                    header = inFile.header)

        # Define our new dimension. Note, this must be done before giving
        # the output file point records.
        outFile.define_new_dimension(
            name = 'total_tpu',
            data_type = 5, description = 'subaerial and subaqueous tpu combined in quadrature')

        for dimension in inFile.point_format:
            dat = inFile.reader.get_dimension(dimension.name)
            outFile.writer.set_dimension(dimension.name, dat)

        outFile.my_special_dimension = range(len(inFile))

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
