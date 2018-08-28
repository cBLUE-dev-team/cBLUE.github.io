# -*- coding: utf-8 -*-
import logging
logging.basicConfig(format='%(asctime)s:%(message)s', level=logging.INFO)

import Tkinter as tk
import os

# Import Gui helper classes
from DirectorySelectButton import DirectorySelectButton
from RadioFrame import RadioFrame

from Sbet import Sbet
from Subaerial import Subaerial
from Subaqueous import Subaqueous
from Datum import Datum
from Tpu import Tpu



class Gui:
    """ Gui used to determine the total propagated
    uncertainty of Lidar Topobathymetry measurements.

    Created: 2017-12-07

    @author: Timothy Kammerer
    """
    
    instance = None

    def __init__(self):
        Gui.instance = self
        self.root = tk.Tk(className=" GUI_topobathy_list")
        self.lastFileLoc = os.getcwd()
        
        # Build the title label
        self.title = tk.Label(text="RIEGL VQ-880-G\n"
                 "TOTAL PROPAGATED UNCERTAINTY (TPU) PROGRAM\n"
                 "v2.0", background="green")
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

        self.is_sbet_loaded = False
        self.buttonEnableStage = 0  # to measure progress through button stages
        self.sbetInput = None
        self.lasInput = None
        self.tpuOutput = None
        self.sbet = None

        #  Build the interface
        self.buildInput()
        self.build_process_buttons()
        
        #  Make the window non-resizable
        self.root.resizable(width=False, height=False)

        # mainloop
        self.root.mainloop()

    def buildInput(self):
        """Builds the input for the Gui.
        """
        self.build_subaerial_input()
        self.build_subaqueous_input()
        self.build_vdatum_input()
    
    def build_subaerial_input(self):
        """Builds the directory selection input and
        processing Buttons for the subaerial portion.
        """

        subaerial_frame = tk.Frame(self.root, borderwidth=2, relief=tk.GROOVE)
        subaerial_frame.grid(row=1)
        tk.Label(subaerial_frame, text="Data Directories",
                 font='Helvetica 10 bold').grid(row=0, columnspan=2, sticky=tk.EW)
        
        button_width = 82
        button_height = 1

        self.sbetInput = DirectorySelectButton(
            self, subaerial_frame, "SBET FILES", button_width,
            button_height, callback=self.updateButtonEnable)
        self.sbetInput.grid(row=2, column=0)

        self.lasInput = DirectorySelectButton(
            self, subaerial_frame, "ORIGINAL LAS TILES", button_width,
            button_height, callback=self.updateButtonEnable)
        self.lasInput.grid(row=3, column=0)

        self.tpuOutput = DirectorySelectButton(
            self, subaerial_frame, "OUTPUT FILES", button_width,
            button_height, callback=self.updateButtonEnable)
        self.tpuOutput.grid(row=4, column=0)

    def build_subaqueous_input(self):
        """Builds the radio button input for the subaqueous portion."""
        # Create Frame
        subaqueous_frame = tk.Frame(self.root, borderwidth=2, relief=tk.GROOVE)
        subaqueous_frame.grid(row=2, sticky=tk.NSEW)

        # Create Frame Label
        tk.Label(subaqueous_frame,
                 text="SUB-AQUEOUS Parameters",
                 font='Helvetica 10 bold').grid(
            row=0, columnspan=2, sticky=tk.EW)

        water_surface_subframe = tk.Frame(subaqueous_frame, borderwidth=2, relief=tk.GROOVE)
        water_surface_subframe.grid(row=1, column=0)

        turbidity_subframe = tk.Frame(subaqueous_frame, borderwidth=2, relief=tk.GROOVE)
        turbidity_subframe.grid(row=1, column=1, sticky=(tk.N, tk.W, tk.E, tk.S))
        turbidity_subframe.columnconfigure(0, weight=1)
        turbidity_subframe.rowconfigure(0, weight=1)

        # Create Radio Buttons
        frameWidth = 40

        self.water_surface_options = [
            "Riegl VQ-880-G",
            "Model (ECKV spectrum)"]

        self.windOptions = [w[0] for w in self.wind_vals.values()]
        self.turbidity_options = ['{:s} ({:.2f}-{:.2f} m^-1)'.format(
            k[0], k[1][0] / 100.0, k[1][-1] / 100.0) for k in self.kd_vals.values()]

        self.waterSurfaceRadio = RadioFrame(
            water_surface_subframe, "Water Surface",
            self.water_surface_options, 1,
            callback=self.updateRadioEnable, width=frameWidth)
        self.waterSurfaceRadio.grid(row=0, column=0, columnspan=2, sticky=tk.W)

        self.windRadio = RadioFrame(water_surface_subframe, None, self.windOptions, 1, width=frameWidth)
        self.windRadio.grid(row=1, column=1, sticky=tk.W)

        self.turbidityRadio = RadioFrame(turbidity_subframe, "Turbidity (kd_490)",
                                         self.turbidity_options, 0, width=frameWidth)
        self.turbidityRadio.grid(row=0, column=0, sticky=tk.N)

    def build_vdatum_input(self):
        datum_frame = tk.Frame(self.root, borderwidth=2, relief=tk.GROOVE)
        datum_frame.grid(row=3, sticky=tk.NSEW)
        tk.Label(datum_frame,
                 text="Regional VDatum Maximum Cumulative Uncertainty (MCU)",
                 font='Helvetica 10 bold').grid(row=2, columnspan=1, sticky=tk.EW)
        datum_transform_subframe = tk.Frame(datum_frame, borderwidth=2, relief=tk.GROOVE)
        datum_transform_subframe.grid(row=3, column=0, columnspan=2, sticky=tk.EW)
        datum_transform_subframe.columnconfigure(0, weight=1)
        datum_transform_subframe.rowconfigure(0, weight=1)
        tk.Label(datum_transform_subframe,
                 text="VDatum Region").grid(row=0, column=0, sticky=tk.EW)

        datum = Datum()
        regions, mcu_values, default_msg = datum.get_vdatum_region_mcus()
        self.vdatum_regions = dict({(key, value) for (key, value) in zip(regions, mcu_values)})
        self.vdatum_regions.update({default_msg: 0})

        self.vdatum_region = tk.StringVar()
        self.vdatum_region.set(default_msg)
        self.vdatum_region_option_menu = tk.OptionMenu(
            datum_transform_subframe,
            self.vdatum_region,
            *sorted(self.vdatum_regions.keys()),
            command=self.updateVdatumMcuValue)
        self.vdatum_region_option_menu.config(width=60)
        self.vdatum_region_option_menu.grid(row=0, column=1)

    def build_process_buttons(self):
        """Builds the process buttons."""

        frame = tk.Frame(self.root, borderwidth=2, relief=tk.GROOVE)
        frame.grid(row=4, sticky=tk.NS)

        tk.Label(frame, text='Process Buttons', font='Helvetica 10 bold').grid(row=0, columnspan=3, sticky=tk.EW)

        button_width = 26
        button_height = 3

        self.sbet_btn_text = tk.StringVar()
        self.sbet_btn_text.set("Load SBET Files")
        self.sbetProcess = tk.Button(frame, textvariable=self.sbet_btn_text,
                                     width=button_width, height=button_height,
                                     state=tk.DISABLED, command=self.sbet_process_callback)
        self.sbetProcess.grid(row=1, column=1)

        self.tpu_btn_text = tk.StringVar()
        self.tpu_btn_text.set("Process TPU")
        self.tpuProcess = tk.Button(frame,
                                    textvariable=self.tpu_btn_text,
                                    width=button_width,
                                    height=button_height,
                                    state=tk.DISABLED,
                                    command=self.tpu_process_callback)
        self.tpuProcess.grid(row=1, column=2)

    '''Button Callbacks'''
    def updateVdatumMcuValue(self, region):
        logging.info(self.vdatum_region.get())
        self.mcu = self.vdatum_regions[region]
        logging.info('The MCU for {} is {} cm.'.format(region, self.mcu))

    def updateButtonEnable(self, newValue=None):
        if newValue == None:
            if self.sbetInput.directoryName != "":
                self.sbetProcess.config(state=tk.ACTIVE)
            if self.tpuOutput.directoryName != "" and self.is_sbet_loaded:
                self.tpuProcess.config(state=tk.ACTIVE)
        else:
            self.buttonEnableStage = newValue

    def sbet_process_callback(self):
        """ Callback for the sbetProcess button."""

        self.sbet = Sbet(self.sbetInput.directoryName)
        self.sbet.set_data()
        self.is_sbet_loaded = True
        self.sbet_btn_text.set(u'{} \u2713'.format(self.sbet_btn_text.get()))
        self.updateButtonEnable()

    def tpu_process_callback(self):
        """Callback for processing tpu and creating outputs."""
        surface_ind = self.waterSurfaceRadio.selection.get()
        surface_selection = self.water_surface_options[surface_ind]

        wind_ind = self.windRadio.selection.get()
        wind_selection = self.windOptions[wind_ind]

        kd_ind = self.turbidityRadio.selection.get()
        kd_selection = self.turbidity_options[kd_ind]

        # get subaqueous         metadata from lookup table header
        subaqueous_f = open('ECKV_look_up_fit_HG0995_1sig.csv', 'r')
        subaqueous_metadata = subaqueous_f.readline().split(',')
        subaqueous_metadata = {k: v.strip() for (k, v) in [n.split(':') for n in subaqueous_metadata]}

        # set rotation matrices and Jacobian (need to do only once)
        R, fR, M = Subaerial.set_rotation_matrices()
        fJ1, fJ2, fJ3, fF = Subaerial.set_jacobian(R, M)

        las_files = [os.path.join(self.lasInput.directoryName, l)
                     for l in os.listdir(self.lasInput.directoryName)
                     if l.endswith('.las')]

        def sbet_tiles_generator():
            """generator that is 2nd argument for the run_tpu_multiprocessing method"""

            tile_size = 500  # meters
            for las in las_files:  # 2016_422000e_2873500n.las
                las_base = las.split('\\')[-1]
                ul_x = float(las_base[5:11])
                ul_y = float(las_base[13:20])
                west = ul_x - tile_size
                east = ul_x + 2 * tile_size
                north = ul_y + tile_size
                south = ul_y - 2 * tile_size

                logging.info('({}) generating SBET tile...'.format(las.split('\\')[-1]))
                yield self.sbet.get_tile(north, south, east, west)

        tpu = Tpu(subaqueous_metadata, surface_selection, surface_ind,
                  wind_selection, self.wind_vals[wind_ind][1], kd_selection,
                  self.kd_vals[kd_ind][1], self.vdatum_region.get(), self.mcu,
                  self.tpuOutput.directoryName, fR, fJ1, fJ2, fJ3, fF)

        tpu.run_tpu_multiprocessing(las_files, sbet_tiles_generator())
        self.tpu_btn_text.set(u'{} \u2713'.format(self.tpu_btn_text.get()))

    def updateRadioEnable(self):
        """Updates the state of the windRadio, depending on waterSurfaceRadio."""
        if self.waterSurfaceRadio.selection.get() == 0:
            self.windRadio.setState(tk.DISABLED)
        else:
            self.windRadio.setState(tk.ACTIVE)


if __name__ == "__main__":
    Gui()
