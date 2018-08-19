import pathos.pools as pp
import os
import time
import Tkinter as tk


class Las:

    def __init__(self):
        pass

    def get_las(self, las):
        from laspy.file import File
        import numpy as np

        print las
        inFile = File(las, mode="r")
        class_codes = {'BATHYMETRY': 26}
        bathy_inds = inFile.raw_classification == class_codes['BATHYMETRY']
        bathy_points = inFile.points[bathy_inds]['point']
        flight_line_ids = np.unique(bathy_points['pt_src_id'])

        for fl in flight_line_ids:
            print '{}...'.format(fl)
            flight_line_indx = bathy_points['pt_src_id'] == fl
            flight_line_bathy = bathy_points[flight_line_indx]
            flight_line_bathy_sorted = np.sort(flight_line_bathy, order='gps_time')
            print flight_line_bathy_sorted[0:1]

    def run(self, las_files):

        total_tic = time.time()

        p = pp.ProcessPool()
        p.map(self.get_las, las_files[20:30])
        p.close()
        p.join()
        print 'TOTAL TIME:', time.time() - total_tic

class Tpu:

    def __init__(
            self,
            sbet_df,
            surface_select,
            surface_ind,
            wind_selection,
            wind_val,
            kd_selection,
            kd_val,
            vdatum_region,
            vdatum_region_mcu,
            tpuOutput):

        self.sbet_df = sbet_df
        self.surface_select = surface_select
        self.surface_ind = surface_ind
        self.wind_selection = wind_selection
        self.wind_val = wind_val
        self.kdSelect = kd_selection
        self.kd_val = kd_val
        self.vdatum_region = vdatum_region
        self.vdatum_region_mcu = vdatum_region_mcu
        self.tpuOutput = tpuOutput

    def multiprocess_tpu(self, las):

        # import these again, here, for multiprocessing
        import Subaerial
        import Subaqueous
        import numpy as np
        import numexpr as ne
        import pandas as pd

        subaerial, flight_lines, poly_surf_errs = Subaerial.main(self.sbet_df, las)

        print('\ncalculating subaqueous TPU component...')
        depth = subaerial[:, 2] + 23
        subaqueous = Subaqueous.main(self.surface_ind, self.wind_val, self.kd_val, depth)

        print('combining subaerial and subaqueous TPU components...')
        vdatum_mcu = float(self.vdatum_region_mcu) / 100  # file is in cm (1-sigma)
        subaerial = subaerial[:, 5]
        # subaerial_95 = ne.evaluate('subaerial * 1.96')  # to standardize to 2 sigma
        # self.subaerial[:, 5] = subaerial_95
        sigma = ne.evaluate('sqrt(subaqueous**2 + subaerial**2 + vdatum_mcu**2)')

        num_points = sigma.shape[0]
        output = np.hstack((
            np.round_(subaerial[:, [0, 1, 2, 5]], decimals=5),
            np.round_(subaqueous.reshape(num_points, 1), decimals=5),
            np.round_(sigma.reshape(num_points, 1), decimals=5),
            flight_lines.reshape(num_points, 1),
            poly_surf_errs))
        print output[0:5, 3:6]
        print sigma

        output_tpu_file = r'{}_TPU.csv'.format(las.split('\\')[-1].replace('.las', ''))
        output_path = '{}\\{}'.format(self.tpuOutput, output_tpu_file)
        output_df = pd.DataFrame(output)

        pkl_path = output_path.replace('csv', 'tpu')
        print('writing TPU to {}'.format(pkl_path))
        output_df.to_pickle(pkl_path)

        # create meta file
        line_sep = '-' * 50
        print('creating TPU meta data file...')
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
        p.map(self.multiprocess_tpu, las_files)
        p.close()
        p.join()



class Gui:
    instance = None

    """
    Initializes the Gui.
    """

    def __init__(self):
        Gui.instance = self
        self.root = tk.Tk(className=" GUI_topobathy_list")
        self.lastFileLoc = os.getcwd()

        # Build the title label
        self.title = tk.Label(
            text="RIEGL VQ-880-G\n"
                 "TOTAL PROPAGATED UNCERTAINTY (TPU) PROGRAM\n"
                 "v2.0",
            background="green")
        self.title.grid(row=0, sticky=tk.EW)

        self.kd_vals = {0: ('Clear', range(6, 11)),
                        1: ('Clear-Moderate', range(11, 18)),
                        2: ('Moderate', range(18, 26)),
                        3: ('Moderate-High', range(26, 33)),
                        4: ('High', range(33, 37))}

        self.wind_vals = {0: ('Calm-light air (0-2 kts)', [1]),
                          1: ('Light Breeze (3-6 kts)', [2, 3]),
                          2: ('Gentle Breeze (7-10 kts)', [4, 5]),
                          3: ('Moderate Breeze (11-15 kts)', [6, 7]),
                          4: ('Fresh Breeze (16-20 kts)', [8, 9, 10])}

        # #  Build the interface
        # self.buildInput()
        self.buildProcessButtons()

        #  Make the window non-resizable
        self.root.resizable(width=False, height=False)

        # mainloop
        self.root.mainloop()

    def buildProcessButtons(self):
        self.isSbetLoaded = False

        frame = tk.Frame(self.root, borderwidth=2, relief=tk.GROOVE)
        frame.grid(row=3, sticky=tk.S)

        # Create Frame Label
        tk.Label(frame, text='Process Buttons', font='Helvetica 10 bold').grid(row=0, columnspan=3, sticky=tk.EW)

        buttonWidth = 26
        buttonHeight = 3

        self.tpu_btn_text = tk.StringVar()
        self.tpu_btn_text.set("Process TPU")
        self.tpuProcess = tk.Button(frame,
                                    textvariable=self.tpu_btn_text,
                                    width=buttonWidth,
                                    height=buttonHeight,
                                    command=self.tpuProcessCallback)
        self.tpuProcess.grid(row=1, column=2)

    def tpuProcessCallback(self):
        # surface_ind = self.waterSurfaceRadio.selection.get()
        # surface_selection = self.waterSurfaceOptions[surface_ind]
        #
        # wind_ind = self.windRadio.selection.get()
        # wind_selection = self.windOptions[wind_ind]
        #
        # kd_ind = self.turbidityRadio.selection.get()
        # kd_selection = self.turbidityOptions[kd_ind]
        #
        # tpu = Tpu(
        #     self.sbet_df,
        #     surface_selection,
        #     surface_ind,
        #     wind_selection,
        #     self.wind_vals[wind_ind][1],
        #     kd_selection,
        #     self.kd_vals[kd_ind][1],
        #     self.vdatum_regions[self.tkvar.get()],
        #     self.mcu,
        #     self.tpuOutput.directoryName)
        #
        # las_files = [os.path.join(self.lasInput.directoryName, l)
        #              for l in os.listdir(self.lasInput.directoryName)
        #              if l.endswith('.las')]
        # tpu.run_tpu_multiprocessing(las_files[28:30])

        las_dir = r'I:\NGS_TPU\DATA\FL1604-TB-N\las'
        las_files = [os.path.join(las_dir, l) for l in os.listdir(las_dir) if l.endswith('.las')]

        l = Las()
        l.run(las_files)



if __name__ == '__main__':
    Gui()


