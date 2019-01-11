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
        
    def calc_tpu(self, sbet_las_tile):
        
        sbet, las = sbet_las_tile

        data_to_pickle = []
        output_columns = []
        
        las = Las(las)
        logging.info('{}\n{}'.format('#' * 30, las.las_short_name))
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
                np.expand_dims(D[1], axis=1),  # las time
                np.round_(subaerial, decimals=5),
                np.round_(np.expand_dims(subaqueous_thu, axis=1), decimals=5),
                np.round_(np.expand_dims(subaqueous_tvu, axis=1), decimals=5),
                np.round_(np.expand_dims(total_thu, axis=1), decimals=5),
                np.round_(np.expand_dims(total_tvu, axis=1), decimals=5),
                ))

            sigma_columns = ['total_thu', 'total_tvu']
            output_columns = ['gps_time'] + subaerial_columns + subaqueous_columns + sigma_columns  # TODO: doesn't need to happen every iteration
            data_to_pickle.append(output)
            stats = ['min', 'max', 'mean', 'std']
            self.flight_line_stats[str(fl)] = pd.DataFrame(
                output, columns=output_columns).describe().loc[stats].to_dict()

        self.write_metadata(las)  # TODO: include as VLR?
        self.output_tpu_to_las_extra_bytes(las, data_to_pickle, output_columns)
        #self.output_tpu_to_pickle(las, data_to_pickle, output_columns)

    def output_tpu_to_pickle(self, las, data_to_pickle, output_columns):
        output_tpu_file = r'{}_TPU.tpu'.format(las.las_base_name)
        output_path = '{}\\{}'.format(self.tpuOutput, output_tpu_file)
        output_df = pd.DataFrame(np.vstack(data_to_pickle), columns=output_columns)
        logging.info('({}) writing TPU...'.format(las.las_short_name))
        output_df.to_pickle(output_path)
        logging.info('finished writing')

    def output_tpu_to_las_extra_bytes(self, las, data_to_pickle, output_columns):
        output_df = pd.DataFrame(np.vstack(data_to_pickle), columns=output_columns)
        output_df = output_df.sort_values(by=['gps_time'])
        #output_df = output_df.drop('gps_time', axis=1)
        decimals = pd.Series([3] * len(output_df.columns), index=output_columns)
        output_df = output_df.round(decimals) * 1000
        output_df = output_df.astype('int64')

        out_las_name = las.las.replace('.las', '_TPU.las')
        logging.info('logging las and tpu results to {}'.format(out_las_name))
        in_las = laspy.file.File(las.las, mode = "r")  # las is Las object
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

        '''populate new extrabyte dimensions; originally, I looped 
        through the items of extra_byte_dimensions using exec(...), 
        but it was to  slow running exec(...); explicity running each 
        command (i.e., without using exec(...)) is noticably faster
        (I think it's faster because it's now not writing the numpy
        array to a list first, which I think was required with 
        exec(...))
        '''
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

        #for dimension, description in extra_byte_dimensions.iteritems():
        #    logging.info('populating extra byte data for {}...'.format(dimension))
        #    extra_byte_data = output_df[dimension].tolist()
        #    command_to_run = 'out_las.{} = {}'.format(dimension, extra_byte_data)
        #    exec(command_to_run)

        # copy data from in_las
        for field in in_las.point_format:
            logging.info('writing {} to {} ...'.format(field.name, out_las))
            dat = in_las.reader.get_dimension(field.name)
            out_las.writer.set_dimension(field.name, dat[las.time_sort_indices])

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

    def run_tpu_multiprocessing(self, sbet_las_tiles):
        p = pp.ProcessPool(4)
        p.imap(self.calc_tpu, sbet_las_tiles)
        p.close()
        p.join()

    def run_tpu_singleprocessing(self, sbet_las_tiles):
        for sbet_las in sbet_las_tiles:
            self.calc_tpu(sbet_las)


if __name__ == '__main__':
    pass
