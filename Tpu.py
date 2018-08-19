


class Tpu:
    def __init__(self, sbet_df, surface_select,
                 surface_ind, wind_selection, wind_val,
                 kd_selection, kd_val, vdatum_region,
                 vdatum_region_mcu, tpu_output):
        self.sbet_df = sbet_df
        self.surface_select = surface_select
        self.surface_ind = surface_ind
        self.wind_selection = wind_selection
        self.wind_val = wind_val
        self.kdSelect = kd_selection
        self.kd_val = kd_val
        self.vdatum_region = vdatum_region
        self.vdatum_region_mcu = vdatum_region_mcu
        self.tpuOutput = tpu_output

    def calc_tpu(self, las):

        # import these again, here, for multiprocessing
        import logging
        logging.basicConfig(format='%(asctime)s:%(message)s', level=logging.INFO)
        import Subaerial
        import Subaqueous
        import numpy as np
        import numexpr as ne
        import pandas as pd








        for l in las_files:
            las = Las(l)

            for fl in las.get_flight_line_ids():
                D = Merge.merge(self.sbet.data, las.get_flight_line_txyz(fl))

                subaerial = Subaerial(D).calc_subaerial()
                subaqueous = Subaqueous(subaerial.tpu)
                datum = Datum()
                total_tpu = Tpu(subaerial.tpu, subaqueous.tpu, datum.tpu)

                # write data to file
                # keep track of metadata stats

            # output metadata file
            output_tpu_file = r'{}_TPU.csv'.format(las.split('\\')[-1].replace('.las', ''))
            output_path = '{}\\{}'.format(self.tpuOutput, output_tpu_file)
            output_df = pd.DataFrame(output)
            pkl_path = output_path.replace('csv', 'tpu')
            logging.info('({}) writing TPU...'.format(las_short_name))
            output_df.to_pickle(pkl_path)






        las_short_name = las.split('\\')[-1]
        logging.info('({})'.format(las_short_name))
        logging.info('({}) calculating subaerial TPU'.format(las_short_name))
        subaerial, flight_lines, poly_surf_errs = Subaerial.main(self.sbet_df, las)
        subaerial_sig_z = subaerial[:, 5]

        logging.info('({}) calculating subaqueous TPU component...'.format(las_short_name))
        depth = subaerial[:, 2] + 23
        subaqueous = Subaqueous.main(self.surface_ind, self.wind_val, self.kd_val, depth)

        logging.info('({}) combining subaerial and subaqueous TPU components...'.format(las_short_name))
        vdatum_mcu = float(self.vdatum_region_mcu) / 100  # file is in cm (1-sigma)
        sigma = ne.evaluate('sqrt(subaqueous**2 + subaerial_sig_z**2 + vdatum_mcu**2)')

        num_points = sigma.shape[0]
        output = np.hstack((
            np.round_(subaerial[:, [0, 1, 2, 5]], decimals=5),
            np.round_(subaqueous.reshape(num_points, 1), decimals=5),
            np.round_(sigma.reshape(num_points, 1), decimals=5),
            flight_lines.reshape(num_points, 1),
            poly_surf_errs))

    def create_metadata(self):
        line_sep = '-' * 50
        logging.info('({}) creating TPU meta data file...'.format(las_short_name))
        meta_str = 'TPU METADATA FILE\n{}\n'.format(las)
        meta_str += '\n{}\n{}\n{}\n'.format(line_sep, 'PARAMETERS', line_sep)

        meta_str += '{:35s}:  {}\n'.format('water surface', self.surface_select)
        meta_str += '{:35s}:  {}\n'.format('wind', self.wind_selection)
        meta_str += '{:35s}:  {}\n'.format('kd', self.kdSelect)
        meta_str += '{:35s}:  {}\n'.format('VDatum region', self.vdatum_region)
        meta_str += '{:<35}:  {} (m)\n'.format('VDatum region MCU', vdatum_mcu)

        meta_str += '\n{}\n{}\n{}\n'.format(
            line_sep, 'TOTAL SIGMA Z TPU (METERS) SUMMARY', line_sep)
        meta_str += '{:10}\t{:10}\t{:10}\t{:10}\t{:10}\t{:10}\n'.format(
            'FIGHT_LINE', 'MIN', 'MAX', 'MEAN', 'STDDEV', 'COUNT')

        output = output.astype(np.float)
        unique_flight_line_codes = np.unique(output[:, 6])

        for u in sorted(unique_flight_line_codes):
            flight_line_tpu = output[output[:, 6] == u][:, 5]

            min_tpu = np.min(flight_line_tpu)
            max_tpu = np.max(flight_line_tpu)
            mean_tpu = np.mean(flight_line_tpu)
            std_tpu = np.std(flight_line_tpu)
            count_tpu = np.count_nonzero(flight_line_tpu)

            meta_str += '{:<10}\t{:<10.5f}\t{:<10.5f}\t{:<10.5f}\t{:<10.5f}\t{}\n'.format(
                int(u), min_tpu, max_tpu, mean_tpu, std_tpu, count_tpu)

        output_tpu_meta_file = r'{}_TPU.meta'.format(las.split('\\')[-1].replace('.las', ''))
        outputMetaFile = open("{}\\{}".format(self.tpuOutput, output_tpu_meta_file), "w")
        outputMetaFile.write(meta_str)
        outputMetaFile.close()

    def run_tpu_multiprocessing(self, las_files):
        p = pp.ProcessPool()
        p.map(self.calc_tpu, las_files)
        p.close()
        p.join()


if __name__ == '__main__':
    pass
