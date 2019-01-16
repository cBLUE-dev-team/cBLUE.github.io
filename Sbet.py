import os
import time
import pandas as pd
from datetime import datetime
import logging


"""
This class provides the functionality to load trajectory data into cBLUE.  One pandas dataframe is
created from the sbet file(s) loaded by the user.
"""


class Sbet:
    def __init__(self, sbet_dir):
        self.sbet_dir = sbet_dir
        self.sbet_files = sorted(['{}\{}'.format(sbet_dir, f) for f in os.listdir(sbet_dir)
                                  if f.endswith('.txt')])
        self.data = None

    @staticmethod
    def get_sbet_date(sbet):
        """parses year, month, and day from ASCII sbet filename

        :param str sbet: ASCII sbet filename
        :return: List[int]
        """
        sbet_parts = sbet.split('\\')
        sbet_name = sbet_parts[-1]
        year = int(sbet_name[0:4])
        month = int(sbet_name[4:6])
        day = int(sbet_name[6:8])
        sbet_date = [year, month, day]
        return sbet_date

    @staticmethod
    def gps_sow_to_gps_adj(gps_date, gps_wk_sec):
        """converts GPS seconds-of-week timestamp to GPS adjusted standard time

        In the case that the timestamps in the sbet files are GPS week seconds,
        this method is called to convert the timestamps to GPS adjusted standard
        time, which is what the las file timestamps are.  The timestamps in the
        sbet and las files need to be the same format, because the merging process
        merges the data in the sbet and las files based on timestamps.

        :param ? gps_date: [year, month, day]
        :param ? gps_wk_sec: GPS seconds-of-week timestamp
        :return: float
        """
        
        logging.info('converting GPS week seconds to GPS adjusted standard time...'),
        SECS_PER_GPS_WK = 7 * 24 * 60 * 60  # 604800 sec
        SECS_PER_DAY = 24 * 60 * 60  # 86400 sec
        GPS_EPOCH = datetime(1980, 1, 6, 0, 0, 0)

        year = gps_date[0]
        month = gps_date[1]
        day = gps_date[2]

        sbet_date = datetime(year, month, day)
        dt = sbet_date - GPS_EPOCH
        gps_wk = int((dt.days * SECS_PER_DAY + dt.seconds) / SECS_PER_GPS_WK)
        gps_time = gps_wk * SECS_PER_GPS_WK + gps_wk_sec
        gps_time_adj = gps_time - 1e9
        return gps_time_adj

    def build_sbets_data(self):
        """builds 1 pandas dataframe from all ASCII sbet files

        :return: pandas dataframe
        """

        sbets_df = pd.DataFrame()
        header_sbet = ['time', 'lon', 'lat', 'X', 'Y', 'Z', 'roll', 'pitch', 'heading',
                       'stdX', 'stdY', 'stdZ', 'stdroll', 'stdpitch', 'stdheading']
        logging.info('getting sbet data from: ')
        for sbet in sorted(self.sbet_files):
            logging.info('{}...'.format(sbet))
            sbet_df = pd.read_table(
                sbet,
                skip_blank_lines=True,
                engine='c',
                delim_whitespace=True,
                header=None,
                names=header_sbet,
                index_col=False)
            logging.info('({} trajectory points)'.format(sbet_df.shape[0]))
            sbet_date = self.get_sbet_date(sbet)
            gps_time_adj = self.gps_sow_to_gps_adj(sbet_date, sbet_df['time'])
            sbet_df['time'] = gps_time_adj
            sbets_df = sbets_df.append(sbet_df, ignore_index=True)
        sbets_data = sbets_df.sort_values(['time'], ascending=[1])
        return sbets_data

    def set_data(self):
        """populates Sbet objects data field with pandas dataframe (when user
        presses the "Load SBET" button)

        :return: n/a
        """
        sbet_tic = time.clock()
        self.data = self.build_sbets_data()  # df
        sbet_toc = time.clock()
        logging.info('It took {:.1f} mins to load sbets.'.format((sbet_toc - sbet_tic) / 60))

    def get_tile_data(self, north, south, east, west):
        """queries the sbet data points that lie within the given las tile bounding coordinates

        One pandas dataframe is created from all of the loaded ASCII sbet files,
        but as each las tile is processed, only the sbet data located within the
        las tile limits are sent to the calc_tpu() method.

        :param float north: northern limit of las tile
        :param float south: southern limit of las tile
        :param float east: eastern limit of las tile
        :param float west: western limit of las tile
        :return: pandas dataframe
        """
        data = self.data[(self.data.Y >= south) & (self.data.Y <= north) &
                         (self.data.X >= west) & (self.data.X <= east)]
        return data


if __name__ == '__main__':
    pass
    # sbet = Sbet('I:\NGS_TPU\DATA\FL1604-TB-N\sbet\New folder')
    # print sbet.data