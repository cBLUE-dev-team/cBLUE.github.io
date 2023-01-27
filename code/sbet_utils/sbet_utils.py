import os
import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

SECS_PER_GPS_WK = 7 * 24 * 60 * 60  # 604800 sec
SECS_PER_DAY = 24 * 60 * 60  # 86400 sec
GPS_EPOCH = datetime(1980, 1, 6, 0, 0, 0)
GPS_ADJUSTED_OFFSET = 1e9


def get_date(sbet):
    """Parse filename date"""

    # normalize path and split on dir seperator
    # We should include logic to check that date is in filename
    sbet_path = os.path.normpath(sbet)
    sbet_parts = os.path.split(sbet_path)

    sbet_name = sbet_parts[-1]

    # Sbet date embedded in file name by convention
    year = int(sbet_name[0:4])
    month = int(sbet_name[4:6])
    day = int(sbet_name[6:8])
    return (year, month, day)


def sow_to_adj(date, gps_wk_sec):
    """Seconds of Week to Adjusted Time"""

    dt = datetime(*date) - GPS_EPOCH
    gps_wk = int((dt.days * SECS_PER_DAY + dt.seconds) / SECS_PER_GPS_WK)
    gps_time = gps_wk * SECS_PER_GPS_WK + gps_wk_sec
    gps_time_adj = gps_time - GPS_ADJUSTED_OFFSET

    return gps_time_adj


def read_sbet(fname):
    """Process ASCII SBET file from PosPac"""

    header_sbet = [
        "time",
        "lon",
        "lat",
        "X",
        "Y",
        "Z",
        "roll",
        "pitch",
        "heading",
        "stdX",
        "stdY",
        "stdZ",
        "stdroll",
        "stdpitch",
        "stdheading",
    ]

    logger.sbet(f"SBET Name : {fname}")
    sbet = pd.read_csv(fname, names=header_sbet, delimiter="\t")

    # Check for gps adjusted time
    if sbet["time"][0] <= SECS_PER_GPS_WK:
        # Reset time to adjusted standard time
        date = get_date(fname)
        sbet["time"] = sbet["time"].apply(lambda t: sow_to_adj(date, t))

    return sbet
