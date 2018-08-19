import os
import time
import pandas as pd
from datetime import datetime


class Sbet:
    def __init__(self, sbet_dir):
        self.sbet_dir = sbet_dir
        self.sbet_files = sorted(['{}\{}'.format(sbet_dir, f) for f in os.listdir(sbet_dir)
                                  if f.endswith('.txt')])

    # get sbet date from file name
    def get_sbet_date(self, sbet):
        sbet_parts = sbet.split('\\')
        sbet_name = sbet_parts[-1]
        year = int(sbet_name[0:4])
        month = int(sbet_name[4:6])
        day = int(sbet_name[6:8])
        sbet_date = [year, month, day]
        return sbet_date

    # convert the GPS seconds-of-week timestamps
    # to GPS adjusted standard time
    def gps_sow_to_gps_adj(self, gps_date, gps_wk_sec):
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

    # build 1 pandas dataframe from all ASCII sbet files
    def build_sbets_data(self):
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

    @property
    def data(self):
        sbet_tic = time.clock()
        sbets_df = self.build_sbets_data()
        sbet_toc = time.clock()
        logging.info('It took {:.1f} mins to load sbets.'.format((sbet_toc - sbet_tic) / 60))
        return sbets_df


if __name__ == '__main__':
    pass
    # sbet = Sbet('I:\NGS_TPU\DATA\FL1604-TB-N\sbet\New folder')
    # print sbet.data