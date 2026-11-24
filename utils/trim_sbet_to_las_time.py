import os
import pandas as pd
import logging
from datetime import datetime
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

SECS_PER_GPS_WK = 7 * 24 * 60 * 60  # 604800 sec
SECS_PER_DAY = 24 * 60 * 60  # 86400 sec
GPS_EPOCH = datetime(1980, 1, 6, 0, 0, 0)
GPS_ADJUSTED_OFFSET = 1e9

def get_sbet_date(sbet):
        """parses year, month, and day from ASCII sbet filename

        :param str sbet: ASCII sbet filename
        :return: List[int]
        """
        sbet_path = os.path.normpath(sbet)
        sbet_parts = os.path.split(sbet_path)

        sbet_name = sbet_parts[-1]
        logger.debug(f"SBET Name : {sbet_name}")
        year = int(sbet_name[0:4])
        month = int(sbet_name[4:6])
        day = int(sbet_name[6:8])
        sbet_date = [year, month, day]
        return sbet_date

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

    logger.debug("converting GPS week seconds to GPS adjusted standard time..."),

    year = gps_date[0]
    month = gps_date[1]
    day = gps_date[2]

    sbet_date = datetime(year, month, day)
    dt = sbet_date - GPS_EPOCH
    gps_wk = int((dt.days * SECS_PER_DAY + dt.seconds) / SECS_PER_GPS_WK)
    gps_time = gps_wk * SECS_PER_GPS_WK + gps_wk_sec
    gps_time_adj = gps_time - GPS_ADJUSTED_OFFSET

    return gps_time_adj

def check_if_sow(time):
    logger.debug("checking if timestamps are GPS week seconds...")
    if time <= SECS_PER_GPS_WK:
        return True
    else:
        return False

if __name__ == "__main__":

    # Example usage
    sbet_path = Path("Path/to/your_file.txt")  # Replace with your actual SBET file path
    sbet_date = get_sbet_date(sbet_path)
    logger.info(f"Parsed SBET date: {sbet_date}")

    las_start_time = 461190653.075818 
    las_end_time = 461191562.074303
    logger.info(f"LAS start time: {las_start_time}, LAS end time: {las_end_time}")

    # Read in the sbet_file and save it to a DataFrame
    sbet_df = pd.read_csv(sbet_path, sep=r"\s+", header=None, index_col=False)

    # Check if the timestamps in the sbet file are GPS week seconds and convert them to GPS adjusted standard time if they are
    is_sow = check_if_sow(sbet_df.iloc[:, 0].iloc[0])
    if is_sow:
        gps_time_adj = gps_sow_to_gps_adj(sbet_date, sbet_df.iloc[:, 0])
        sbet_df.iloc[:, 0] = gps_time_adj
    logger.info(f"Converted SBET timestamps to GPS adjusted standard time: {sbet_df.iloc[:, 0].head()}")
    logger.info(f"SBET DataFrame shape: {sbet_df.shape}")

    # Trim the sbet DataFrame to only include rows with timestamps between the las start and end times
    trimmed_sbet_df = sbet_df[(sbet_df.iloc[:, 0] >= las_start_time) & (sbet_df.iloc[:, 0] <= las_end_time)]

    logger.info(f"Trimmed SBET DataFrame to include only rows with timestamps between {las_start_time} and {las_end_time}. Number of rows after trimming: {len(trimmed_sbet_df)}") 

    trimmed_sbet_filename = sbet_path.with_name(
        f"{sbet_path.stem}_trimmed{sbet_path.suffix}"
    )

    trimmed_sbet_df.to_csv(
        trimmed_sbet_filename,
        sep="\t",
        header=False,
        index=False
    )

