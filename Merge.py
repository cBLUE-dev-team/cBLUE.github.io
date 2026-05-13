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
204 Owen Hall
Oregon State University
Corvallis, OR  97331
(541) 737-5688
christopher.parrish@oregonstate.edu

Last Edited By:
Keana Kief (OSU)
May 12th, 2026

"""

import numpy as np
import numexpr as ne
from math import radians
import logging

logger = logging.getLogger(__name__)


class Merge:

    max_allowable_dt = 1.0  # second

    def __init__(self, sensor_object):
        self.a_std_dev = sensor_object.a_std_dev  # degrees
        self.b_std_dev = sensor_object.b_std_dev  # degrees
        self.std_rho = sensor_object.std_rho

    @staticmethod
    def _print_match_debug(label, t_las, fl_las_data, idx, mask, t_sbet, idx_out, *,
                           target=None, tol_t=1e-7, tol_xy=1e-2, tol_z=1e-2):
        """Optional debug printer for a target point.

        target:
          - None (no debug)
          - float (GPS time)
          - tuple (t, x, y, z) to uniquely identify a point
        """
        if target is None:
            return

        if isinstance(target, (float, int)):
            matches = np.where(np.isclose(t_las, float(target), atol=tol_t))[0]
        else:
            tt, xx, yy, zz = target
            matches = np.where(
                np.isclose(t_las, tt, atol=tol_t)
                & np.isclose(fl_las_data[:, 0], xx, atol=tol_xy)
                & np.isclose(fl_las_data[:, 1], yy, atol=tol_xy)
                & np.isclose(fl_las_data[:, 2], zz, atol=tol_z)
            )[0]

        if not matches.size:
            print(f"\nDEBUG({label}): target not present in this flightline array")
            return

        i = int(matches[0])
        print(f"\nDEBUG({label}):")
        print(" LAS t,x,y,z:", float(t_las[i]), float(fl_las_data[i, 0]), float(fl_las_data[i, 1]), float(fl_las_data[i, 2]))
        print(" initial idx:", int(idx[i]))

        if 0 < idx[i] < len(t_sbet):
            print(" SBET prev:", float(t_sbet[idx[i]-1]))
            print(" SBET next:", float(t_sbet[idx[i]]))
            print(" dt prev:", float(t_sbet[idx[i]-1] - t_las[i]))
            print(" dt next:", float(t_sbet[idx[i]] - t_las[i]))
        else:
            print(" OUT OF RANGE")

        if idx_out is not None:
            if bool(mask[i]):
                print(" FINAL SBET idx:", int(idx_out[i]))
                print(" FINAL SBET time:", float(t_sbet[int(idx_out[i])]))
                print(" FINAL dt:", float(t_sbet[int(idx_out[i])] - t_las[i]))
            else:
                print(" point masked out")

    def match_timestamps(
        self,
        sbet_data,
        fl_las_data,
        *,
        time_round_decimals=7,
        tie_eps=1e-9,
        debug_target=None
    ):
        """
        Deterministic SBET↔LAS timestamp matching.

        1) Match by time using integer ticks (avoids float jitter).
        2) If multiple SBET rows share the chosen tick, break ties by spatial proximity
        between LAS xyz and SBET xyz.

        Assumes SBET columns:
        time: col 0
        x,y,z: cols 3,4,5   (as used later in merge())
        LAS flightline array columns:
        x,y,z: cols 0,1,2
        time: col 3
        """

        # --- float times for dt output ---
        t_sbet_f = np.asarray(sbet_data[:, 0])
        t_las_f  = np.asarray(fl_las_data[:, 3])

        # --- integer ticks for matching ---
        scale = int(10 ** int(time_round_decimals))
        t_sbet_i = np.round(t_sbet_f * scale).astype(np.int64)
        t_las_i  = np.round(t_las_f  * scale).astype(np.int64)

        # --- SBET sort by time ticks (stable) ---
        order = np.argsort(t_sbet_i, kind="mergesort")
        t_sbet_i_s = t_sbet_i[order]
        t_sbet_f_s = t_sbet_f[order]

        # SBET positions in the same sorted order
        xs_s = np.asarray(sbet_data[:, 3])[order]
        ys_s = np.asarray(sbet_data[:, 4])[order]
        zs_s = np.asarray(sbet_data[:, 5])[order]

        # LAS positions
        xl = np.asarray(fl_las_data[:, 0])
        yl = np.asarray(fl_las_data[:, 1])
        zl = np.asarray(fl_las_data[:, 2])

        # --- time match using searchsorted ---
        idx = np.searchsorted(t_sbet_i_s, t_las_i, side="left")

        mask = (idx > 0) & (idx < len(t_sbet_i_s))

        # DEBUG (PRE): show neighbors using *sorted* SBET float times
        self._print_match_debug(
            "pre-nearest",
            t_las_f,              # float LAS time for printing
            fl_las_data,          # so (t,x,y,z) matching works
            idx,
            mask,
            t_sbet_f_s,           # SBET times in sorted space for prev/next display
            None,
            target=debug_target
        )


        if not np.any(mask):
            return idx, mask, np.array([])

        idx_m = np.clip(idx, 1, len(t_sbet_i_s) - 1)

        prev_i = t_sbet_i_s[idx_m - 1]
        next_i = t_sbet_i_s[idx_m]
        d_prev = np.abs(t_las_i - prev_i)
        d_next = np.abs(next_i - t_las_i)

        tie_eps_ticks = int(round(float(tie_eps) * scale))
        use_prev = (d_prev < d_next) | (np.abs(d_prev - d_next) <= tie_eps_ticks)
        idx_m = idx_m.copy()
        idx_m[use_prev] -= 1

        # idx_s is the chosen SBET index in *sorted* SBET space
        idx_s = idx_m

        # --- DISAMBIGUATE duplicate SBET ticks by spatial proximity ---
        chosen_tick = t_sbet_i_s[idx_s]

        # for each chosen tick, find its [left,right) run of equal ticks
        left = np.searchsorted(t_sbet_i_s, chosen_tick, side="left")
        right = np.searchsorted(t_sbet_i_s, chosen_tick, side="right")
        dup = (right - left) > 1

        # only loop over the ambiguous (duplicate) matches — typically small
        dup_idx = np.where(mask & dup)[0]
        for j in dup_idx:
            l = int(left[j]); r = int(right[j])
            # candidates are SBET rows with exactly the same time tick
            dx = xs_s[l:r] - xl[j]
            dy = ys_s[l:r] - yl[j]
            dz = zs_s[l:r] - zl[j]
            k = int(np.argmin(dx*dx + dy*dy + dz*dz))
            idx_s[j] = l + k  # best candidate in sorted SBET space

        # map from sorted SBET space back to original SBET indices
        idx_out = idx.copy()
        idx_out[mask] = order[idx_s[mask]]

        # --- optional debug (time or (t,x,y,z)) using your helper if you want ---
        # if you want to keep your existing debug helper, call it here.
        
        # DEBUG (POST): show FINAL using original SBET float times
        self._print_match_debug(
            "post-nearest",
            t_las_f,
            fl_las_data,
            idx,
            mask,
            t_sbet_f,             # original SBET times so FINAL SBET time prints correctly
            idx_out,
            target=debug_target
        )

        if debug_target is not None:
            tt, xx, yy, zz = debug_target
            m = np.where(
                np.isclose(t_las_f, tt, atol=1e-7) &
                np.isclose(fl_las_data[:,0], xx, atol=1e-2) &
                np.isclose(fl_las_data[:,1], yy, atol=1e-2) &
                np.isclose(fl_las_data[:,2], zz, atol=1e-2)
            )[0]
            if m.size:
                i = int(m[0])
                if mask[i]:
                    k = int(idx_out[i])
                    print("SBET_CHOSEN idx=", k,
                        "XYZ=", float(sbet_data[k,3]), float(sbet_data[k,4]), float(sbet_data[k,5]),
                        "RPH=", float(sbet_data[k,6]), float(sbet_data[k,7]), float(sbet_data[k,8]),
                        "STDxyz=", float(sbet_data[k,9]), float(sbet_data[k,10]), float(sbet_data[k,11]),
                        "STDrph=", float(sbet_data[k,12]), float(sbet_data[k,13]), float(sbet_data[k,14]))


        dt = t_sbet_f[idx_out[mask]] - t_las_f[mask]
        max_dt = np.max(np.abs(dt)) if dt.size else np.array([])

        return idx_out, mask, max_dt



    def merge(self, las_short_name, fl, sbet_data, fl_unsorted_las_xyztcf, fl_las_idx, sensor_object,
              *, context_label="", debug_target=None,
              time_round_decimals=7, tie_eps=1e-9):
        """returns sbet & las data merged based on timestamps

        The cBLUE TPU calculations require the sbet and las data to be in
        a single array, so the sbet and lidar data, which are contained in
        separate files, are 'merged', based on time.  cBLUE uses the numpy
        searchsorted function to match lidar datapoints with the nearest-in-time
        (with sorter='left') sbet datapoints.

        If the delta_t between any of the matched datapoints is > 1, TPU is
        not calculated.  Future versions might be smart enough to exclude only
        the offending datapoints rather than discarding the whole file, but for
        the time being, if a single datapoint's delta_t exceeds the allowable
        maximum dt, the entire line is ignored.

        Parameters
        ----------
        sbet_data : ndarray
            SBET data.
        fl_unsorted_las_xyztcf : ndarray
            Flightline LAS-derived array, columns: x,y,z,t,classification, ...
        fl_las_idx : ndarray[int]
            Original LAS point indices for write-back.
        sensor_object : object
            Sensor info.
        context_label : str
            Optional label for logs (e.g., f"{las_short_name} FL {fl}").
        debug_target : None | float | (t,x,y,z)
            Optional debug selector.
        time_round_decimals : int
            Decimal rounding for LAS time used in matching.
        tie_eps : float
            Tolerance for deterministic tie-break.

        Returns
        -------
        (data, stddev, fl_las_idx_masked, raw_class, masked_fan_angle, masked_hawkeye_data)
        The following table lists the contents of the returned list of ndarrays:

        =====   =========   ========================    =======
        Index   ndarray     description                 units
        =====   =========   ========================    =======
        0       t_sbet      sbet timestamps
        1       t_las       las timestamps
        2       x_las       las x coordinates
        3       y_las       las y coordinates
        4       z_las       las z coordinates
        5       x_sbet      sbet x coordinates
        6       y_sbet      sbet y coordinates
        7       z_sbet      sbet z coordinates
        8       r           sbet roll
        9       p           sbet pitch
        10      h           sbet heading
        11      std_a       a uncertainty
        12      std_b       b uncertainty
        13      std_r       sbet roll uncertainty
        14      std_p       sbet pitch uncertainty
        15      std_h       sbet heading uncertainty
        16      stdx_sbet   sbet x uncertainty
        17      stdy_sbet   sbet y uncertainty
        18      stdz_sbet   sbet z uncertainty
        =====   =========   ========================    =======
        """

        num_sbet_pts = sbet_data.shape[0]
        if hasattr(logger, "merge"):
            logger.merge(f"Num SBET points: {num_sbet_pts}")
        else:
            logger.info(f"Num SBET points: {num_sbet_pts}")

        # Deterministic sort by point values: time primary, x/y/z tie-break.
        t = fl_unsorted_las_xyztcf[:, 3]
        x = fl_unsorted_las_xyztcf[:, 0]
        y = fl_unsorted_las_xyztcf[:, 1]
        z = fl_unsorted_las_xyztcf[:, 2]

        sort_idx = np.argsort(
            np.round(t, 9),
            kind="mergesort"   # STABLE SORT
        )

        fl_las_data = fl_unsorted_las_xyztcf[sort_idx]
        fl_las_idx = fl_las_idx[sort_idx]

        # Try to match sbet and las dfs based on timestamps
        idx, mask, max_dt = self.match_timestamps(
            sbet_data,
            fl_las_data,
            time_round_decimals=time_round_decimals,
            tie_eps=tie_eps,
            debug_target=debug_target,
        )

        # If max_dt is too large or empty, then we cannot merge the data. 
        # This is likely due to the LAS data being standard gps time, when we expect adjusted standard gps time.
        # Attempt time conversions and re-match.
        if (isinstance(max_dt, np.ndarray) and max_dt.size == 0) or (not isinstance(max_dt, np.ndarray) and max_dt > self.max_allowable_dt):
            # Standard GPS -> Adjusted Standard
            fl_las_data = fl_las_data.copy()
            fl_las_data[:, 3] = fl_las_data[:, 3] - 1e9
            idx, mask, max_dt = self.match_timestamps(
                sbet_data,
                fl_las_data,
                time_round_decimals=time_round_decimals,
                tie_eps=tie_eps,
                debug_target=debug_target,
            )

            if (isinstance(max_dt, np.ndarray) and max_dt.size == 0) or (not isinstance(max_dt, np.ndarray) and max_dt > self.max_allowable_dt):
                # UTC -> Adjusted (approx by adding 18s after -1e9)
                fl_las_data[:, 3] = fl_las_data[:, 3] + 18
                idx, mask, max_dt = self.match_timestamps(
                    sbet_data,
                    fl_las_data,
                    time_round_decimals=time_round_decimals,
                    tie_eps=tie_eps,
                    debug_target=debug_target,
                )

                if (isinstance(max_dt, np.ndarray) and max_dt.size == 0) or (not isinstance(max_dt, np.ndarray) and max_dt > self.max_allowable_dt):
                    logging.warning("trajectory and LAS data NOT MERGED")
                    if context_label:
                        logging.warning(f"({context_label}) max_dt: {max_dt}")
                    else:
                        logging.warning("({} FL {}) max_dt: {}".format(las_short_name, fl, max_dt))

                    data = False
                    stddev = False
                    raw_class = False
                    masked_fan_angle = False
                    masked_hawkeye_data = False

                    return (
                        data,
                        stddev,
                        fl_las_idx[mask],
                        raw_class,
                        masked_fan_angle,
                        masked_hawkeye_data,
                    )

        data = np.asarray(
            [
                sbet_data[:, 0][idx[mask]],              # t_sbet
                fl_las_data[:, 3][mask],                 # t_las
                fl_las_data[:, 0][mask],                 # x_las
                fl_las_data[:, 1][mask],                 # y_las
                fl_las_data[:, 2][mask],                 # z_las
                sbet_data[:, 3][idx[mask]],              # x_sbet
                sbet_data[:, 4][idx[mask]],              # y_sbet
                sbet_data[:, 5][idx[mask]],              # z_sbet
                np.radians(sbet_data[:, 6][idx[mask]]),  # roll
                np.radians(sbet_data[:, 7][idx[mask]]),  # pitch
                np.radians(sbet_data[:, 8][idx[mask]]),  # heading
            ]
        )

        num_points = data[0].shape

        stddev = np.vstack(
            [
                np.full(num_points, radians(self.a_std_dev)),  # std_a
                np.full(num_points, radians(self.b_std_dev)),  # std_b
                np.radians(sbet_data[:, 12][idx[mask]]),  # std_r
                np.radians(sbet_data[:, 13][idx[mask]]),  # std_p
                np.radians(sbet_data[:, 14][idx[mask]]),  # std_h
                sbet_data[:, 9][idx[mask]],  # stdx_sbet
                sbet_data[:, 10][idx[mask]],  # stdy_sbet
                sbet_data[:, 11][idx[mask]],  # stdz_sbet
                np.full(num_points, self.std_rho),  # std_rho
            ]
        )

        raw_class = fl_las_data[:, 4][mask]

        masked_fan_angle = []
        masked_hawkeye_data = []

        # If this is a multi beam sensor, use the mask on the fan angle array 
        if(sensor_object.type == "multi"):
            masked_fan_angle = fl_las_data[:, 5][mask]
            #Take the absolute value of the fan angle
            masked_fan_angle = np.absolute(masked_fan_angle)
            #Round fan angle to the nearest integer
            #   Adding 0.5 and flooring the value gives consistant rounding up on a half value. 
            #   numpy's rint rounds to the nearest even value, which is an undesired outcome in this case, so it is not used here.
            masked_fan_angle = np.floor(masked_fan_angle + 0.5).astype(int)

            # Unbounded scan angle/fan angle can go past 26 degrees (absolute). 
            # Warn the user if their fan angle exceed maximum allowed fan angle.
            if not all(i <= 26 for i in masked_fan_angle):
                if hasattr(logger, "merge"):
                    logger.merge("WARNING: A scan angle exceeds an absolute value of 26 degrees. Subaqueous processing will fail.")
                else:
                    logger.warning("A scan angle exceeds an absolute value of 26 degrees. Subaqueous processing will fail.")

        elif sensor_object.type == "single_hawkeye":
            masked_hawkeye_data = np.asarray(
                [
                    fl_las_data[:, 5][mask], # masked scanner_channel
                    fl_las_data[:, 6][mask]  # masked user_data
                ]
            )

            # print(f"masked_hawkeye_data: {masked_hawkeye_data}")

        # logger.merge(f"raw fan angle: {fl_las_data[:, 5]}")
        # logger.merge(f"processed fan angle: {masked_fan_angle}")

        return (
            data,
            stddev,
            fl_las_idx[mask],
            raw_class,
            masked_fan_angle,
            masked_hawkeye_data
        )  # 3rd to last array is masked t_idx


if __name__ == "__main__":
    pass
