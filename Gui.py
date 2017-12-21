# -*- coding: utf-8 -*-
# Import Statements
import Tkinter as tk
import os
import numpy as np
import webbrowser
import pandas as pd

# Import Gui helper classes
from DirectorySelectButton import DirectorySelectButton
from RadioFrame import RadioFrame


# Import Processing code
import load_sbet
import pre_TPU_tile_processing
import calc_aerial_TPU
import SubAqueous

"""
Gui used to determine the total propagated 
uncertainty of Lidar Topobathymetry measurements.

Created: 2017-12-07

@author: Timothy Kammerer
"""


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
                 "v1.0",
            background="green")
        self.title.grid(row=0, sticky=tk.EW)
        
        #  Build the interface
        self.buildInput()
        self.buildProcessButtons()
        
        #  Make the window non-resizable
        self.root.resizable(width=False, height=False)
        
        # mainloop
        self.root.mainloop()
    
    #%% GUI Building
    """
    Builds the input for the Gui.
    """
    def buildInput(self):
        self.buildSubaerialInput()
        self.buildParametersInput()
    
    """
    Builds the directory selection input and 
    processing Buttons for the subaerial portion.
    """
    def buildSubaerialInput(self):
        # Create Frame
        frame = tk.Frame(
            self.root, 
            borderwidth=2, 
            relief=tk.GROOVE)
        
        frame.grid(row=1)
        
        #Create Frame Label
        tk.Label(frame,
                 text="Data Directories",
                 font='Helvetica 10 bold').grid(
            row=0,
            columnspan=3,
            sticky=tk.EW)
        
        # Create variable to measure progress through button stages
        self.buttonEnableStage = 0
        
        # Create Directory Inputs
        buttonWidth = 82
        buttonHeight = 1

        self.lastoolsInput = DirectorySelectButton(
            self,
            frame,
            "LAS TOOLS BIN",
            buttonWidth,
            buttonHeight,
            callback=self.updateButtonEnable)
        self.lastoolsInput.grid(row=1, column=0)

        self.lasInput = DirectorySelectButton(
            self,
            frame,
            "ORIGINAL LAS TILES",
            buttonWidth,
            buttonHeight,
            callback=self.updateButtonEnable)
        self.lasInput.grid(row=2, column=0)

        self.sbetInput = DirectorySelectButton(
            self,
            frame,
            "SBET FILES",
            buttonWidth,
            buttonHeight,
            callback=self.updateButtonEnable)
        self.sbetInput.grid(row=4, column=0)

        self.lasSplitTileInput = DirectorySelectButton(
            self,
            frame,
            "FLIGHT LINE BATHY TILES",
            buttonWidth,
            buttonHeight,
            callback=self.updateButtonEnable)
        self.lasSplitTileInput.grid(row=3, column=0)
        
    """
    Builds the radio button input for the subaqueous portion.
    """
    def buildParametersInput(self):
        # Create Frame
        parameters_frame = tk.Frame(
            self.root,
            borderwidth=2,
            relief=tk.GROOVE)
        parameters_frame.grid(
            row=2,
            sticky=tk.NSEW)

        # Create Frame Label
        tk.Label(parameters_frame,
                 text="SUB-AQUEOUS Parameters",
                 font='Helvetica 10 bold').grid(
            row=0,
            columnspan=2,
            sticky=tk.EW)

        water_surface_subframe = tk.Frame(
            parameters_frame,
            borderwidth=2,
            relief=tk.GROOVE,)
        water_surface_subframe.grid(
            row=1,
            column=0)

        turbidity_subframe = tk.Frame(
            parameters_frame,
            borderwidth=2,
            relief=tk.GROOVE)
        turbidity_subframe.grid(
            row=1,
            column=1,
            sticky=(tk.N, tk.W, tk.E, tk.S))
        turbidity_subframe.columnconfigure(0, weight=1)
        turbidity_subframe.rowconfigure(0, weight=1)

        tk.Label(parameters_frame,
                 text="Vertical Datum Transformation Parameters",
                 font='Helvetica 10 bold').grid(
            row=2,
            columnspan=2,
            sticky=tk.EW)

        datum_transform_subframe = tk.Frame(
            parameters_frame,
            borderwidth=2,
            relief=tk.GROOVE)
        datum_transform_subframe.grid(
            row=3,
            column=0,
            columnspan=2,
            sticky=tk.EW)
        datum_transform_subframe.columnconfigure(0, weight=1)
        datum_transform_subframe.rowconfigure(0, weight=1)

        # Create Radio Buttons
        frameWidth = 40

        self.waterSurfaceOptions = [
            "Riegl VQ-880-G",
            "Model (ECKV spectrum)"]

        self.windOptions = [
            "Calm-Light air (0-3 knots)",
            "Light breeze (3-6 knots)",
            "Gentle Breeze (6-10 knots)",
            "Moderate Breeze (10-15 knots)",
            "Fresh Breeze (15-20 knots)"]

        self.turbidityOptions = [
            "Clear",
            "Clear-Moderate",
            "Moderate",
            "Moderate-High",
            "High"]

        self.waterSurfaceRadio = RadioFrame(
            water_surface_subframe,
            "Water Surface",
            self.waterSurfaceOptions,
            1,
            callback=self.updateRadioEnable,
            width=frameWidth)
        self.waterSurfaceRadio.grid(
            row=0,
            column=0,
            columnspan=2,
            sticky=tk.W)

        self.windRadio = RadioFrame(
            water_surface_subframe,
            None,
            self.windOptions,
            1,
            width=frameWidth)
        self.windRadio.grid(
            row=1,
            column=1,
            sticky=tk.W)

        self.turbidityRadio = RadioFrame(
            turbidity_subframe,
            "Turbidity",
            self.turbidityOptions,
            0,
            width=frameWidth)
        self.turbidityRadio.grid(
            row=0,
            column=0,
            sticky=tk.N)
        # List with options

        tk.Label(
            datum_transform_subframe,
            text="VDatum Region").grid(
            row=0,
            column=0,
            sticky=tk.EW)

        vdatum_regions_MCU_file = r'I:\NGS_TPU\NGS_TPU_TOOL\V_Datum_MCU_Values.txt'
        vdatum_regions_file_obj = open(vdatum_regions_MCU_file, 'r')
        vdatum_regions = vdatum_regions_file_obj.readlines()
        vdatum_regions_file_obj.close()

        # clean up vdatum file; when copying table from internet, some dashes
        # are 'regular dashes' and others are \x96; get rid of quotes and \n

        vdatum_regions = [v.replace('\x96', '-') for v in vdatum_regions]
        vdatum_regions = [v.replace('"', '') for v in vdatum_regions]
        vdatum_regions = [v.replace('\n', '') for v in vdatum_regions]
        regions = [v.split('\t')[0] for v in vdatum_regions]
        mcu_values = [v.split('\t')[1] for v in vdatum_regions]
        self.vdatum_regions = dict({(key, value) for (key, value) in zip(regions, mcu_values)})

        self.tkvar = tk.StringVar(self.root)
        self.tkvar.set('(Choose a region)')  # set the default option
        self.vdatum_region_option_menu = tk.OptionMenu(
            datum_transform_subframe,
            self.tkvar,
            *sorted(self.vdatum_regions.keys()),
            command=self.updateVdatumMcuValue)
        self.vdatum_region_option_menu.config(width=60)
        self.vdatum_region_option_menu.grid(
            row=0,
            column=1)

    """
    Builds the process buttons.
    """
    def buildProcessButtons(self):

        self.isPreProcessed = False
        self.isSbetLoaded = False

        frame = tk.Frame(
            self.root,
            borderwidth=2,
            relief=tk.GROOVE)
        frame.grid(row=3, sticky=tk.S)

        # Create Frame Label
        tk.Label(
            frame,
            text='Process Buttons',
            font='Helvetica 10 bold').grid(
            row=0,
            columnspan=3,
            sticky=tk.EW)

        buttonWidth = 26
        buttonHeight = 3

        self.las_btn_text = tk.StringVar()
        self.las_btn_text.set("Pre-Process Tiles")
        self.lasProcess = tk.Button(
            frame,
            textvariable=self.las_btn_text,
            width=buttonWidth,
            height=buttonHeight,
            state=tk.DISABLED,
            command=self.lasProcessCallback)
        self.lasProcess.grid(row=1, column=0)

        self.sbet_btn_text = tk.StringVar()
        self.sbet_btn_text.set("Load SBET Files")
        self.sbetProcess = tk.Button(
            frame,
            textvariable=self.sbet_btn_text,
            width=buttonWidth,
            height=buttonHeight,
            state=tk.DISABLED,
            command=self.sbetProcessCallback)
        self.sbetProcess.grid(row=1, column=1)

        self.tpu_btn_text = tk.StringVar()
        self.tpu_btn_text.set("Process TPU")
        self.tpuProcess = tk.Button(
            frame,
            textvariable=self.tpu_btn_text,
            width=buttonWidth,
            height=buttonHeight,
            state=tk.DISABLED,
            command=self.tpuProcessCallback)
        self.tpuProcess.grid(row=1, column=2)

    # Button Callbacks
    def updateVdatumMcuValue(self):
        # get VDatum region MCU
        region = self.tkvar.get()
        print('REGION: {}'.format(region))
        mcu = self.vdatum_regions[region]
        print('The MCU for {} is {} cm.'.format(self.tkvar, mcu))


    def updateButtonEnable(self, newValue = None):
        if newValue == None:

            if self.lasInput.directoryName != "" \
                    and self.lastoolsInput.directoryName != "":
                self.lasProcess.config(state=tk.ACTIVE)

            if self.sbetInput.directoryName != "":
                self.sbetProcess.config(state=tk.ACTIVE)

            if self.lasSplitTileInput.directoryName != "" \
                    and self.isPreProcessed \
                    and self.isSbetLoaded:
                self.tpuProcess.config(state=tk.ACTIVE)

        else:
            self.buttonEnableStage = newValue

    """
    Callback for the lasProcess button.
    """
    def lasProcessCallback(self):
        pre_TPU_tile_processing.main(
            self.lastoolsInput.directoryName,
            self.lasInput.directoryName)
        self.isPreProcessed = True
        self.las_btn_text.set(u'{} \u2713'.format(self.las_btn_text.get()))
        self.updateButtonEnable()

    """
    Callback for the sbetProcess button.
    """
    def sbetProcessCallback(self):
        self.sbets_df = load_sbet.main(self.sbetInput.directoryName)
        self.isSbetLoaded = True
        self.sbet_btn_text.set(u'{} \u2713'.format(self.sbet_btn_text.get()))
        self.updateButtonEnable()

    """
    Callback for processing the subaqueous data and inputs and creating outputs.
    """
    def tpuProcessCallback(self):

        orig_tiles = [
            f.split('.')[0] for f in os.listdir(self.lasInput.directoryName)
            if f.endswith('.las')]

        split_las_files = [
            f for f in os.listdir(self.lasSplitTileInput.directoryName)
            if f.endswith('.las')]

        for ot in orig_tiles:

            '''
            get bathy-only flight-line las files
            corresponding to each original tile
            '''
            las_to_process = []
            for slf in split_las_files:
                if slf.startswith(ot):
                    las = r'{}\{}'.format(self.lasSplitTileInput.directoryName, slf)
                    print('LAS:  {}'.format(las))
                    las_to_process.append(las)

            self.subaerial, self.flight_lines = calc_aerial_TPU.main(
                self.sbets_df, las_to_process)
            windSelect = self.windRadio.selection.get()
            kdSelect = self.turbidityRadio.selection.get()

            # Get the wind value from the GUI
            if windSelect == 0:
                wind = [1]
            elif windSelect == 1:
                wind = [2, 3]
            elif windSelect == 2:
                wind = [4, 5]
            elif windSelect == 3:
                wind = [6, 7, 8]
            elif windSelect == 4:
                wind = [9, 10]

            # Get the Kd value from the GUI
            if kdSelect == 0:
                kd = range(5, 11)
            elif kdSelect == 1:
                kd = range(11, 18)
            elif kdSelect == 2:
                kd = range(18, 26)
            elif kdSelect == 3:
                kd = range(26, 33)
            elif kdSelect == 4:
                kd = range(33, 41)

            print('calculating subaqueous TPU component...')
            depth = self.subaerial[:, 2] + 23
            subaqueous = SubAqueous.main(
                self.waterSurfaceRadio.selection.get(), wind, kd, depth)

            print('combining subaerial and subaqueous TPU components...')
            sigma = np.sqrt(subaqueous**2 + self.subaerial[:, 5]**2)
            num_points = sigma.shape[0]

            output = np.hstack((
                np.round_(self.subaerial[:, [0,1,2,5]], decimals=3),
                np.round_(subaqueous.reshape(num_points, 1), decimals=3),
                np.round_(sigma.reshape(num_points, 1), decimals=3),
                self.flight_lines.reshape(num_points, 1)))

            output_tpu_file = r'{}_TPU.csv'.format(ot)
            output_path ='{}\\{}'.format(
                self.lasInput.directoryName, output_tpu_file)
            print('writing TPU to {}'.format(output_path))
            output_df = pd.DataFrame(output)
            output_df.to_csv(output_path, index=False)

            # create meta file
            line_sep = '-' * 50
            print('creating TPU meta data file...')
            meta_str = '{} TPU METADATA FILE\n'.format(ot)
            meta_str += '\n{}\n{}\n{}\n'.format(
                line_sep, 'SUB-AQUEOUS PARAMETERS', line_sep)

            meta_str += '{:15s}:  {}\n'.format(
                'water surface',
                self.waterSurfaceOptions[self.waterSurfaceRadio.selection.get()])
            meta_str += '{:15s}:  {}\n'.format(
                'wind',
                self.windOptions[windSelect])
            meta_str += '{:15s}:  {}\n'.format(
                'kd',
                self.turbidityOptions[kdSelect])

            meta_str += '\n{}\n{}\n{}\n'.format(
                line_sep, 'COMBINED SIGMA Z TPU (METERS) SUMMARY', line_sep)
            meta_str += '{:10}\t{:10}\t{:10}\t{:10}\t{:10}\t{:10}\n'.format(
                'FILE ID', 'MIN', 'MAX', 'MEAN', 'STDDEV', 'COUNT')

            output = output.astype(np.float)
            unique_flight_line_codes = np.unique(output[:, 6])
            print(unique_flight_line_codes)

            for u in sorted(unique_flight_line_codes):
                flight_line_tpu = output[output[:, 6] == u][:, 5]

                min_tpu = np.min(flight_line_tpu)
                max_tpu = np.max(flight_line_tpu)
                mean_tpu = np.mean(flight_line_tpu)
                std_tpu = np.std(flight_line_tpu)
                count_tpu = np.count_nonzero(flight_line_tpu)

                meta_str += '{:<10}\t{:<10.3f}\t{:<10.3f}\t{:<10.3f}\t{:<10.3f}\t{}\n'.format(
                    int(u), min_tpu, max_tpu, mean_tpu, std_tpu, count_tpu)

            meta_str += '\n{}\n{}\n{}\n'.format(
                line_sep, 'FILE IDS (BATHY-ONLY FLIGHT-LINE FILES)', line_sep)
            for j, l in enumerate(las_to_process):
                meta_str += '{} - {}\n'.format(j, l)

            output_tpu_meta_file = r'{}_TPU.meta'.format(ot)
            outputMetaFile = open("{}\\{}".format(
                self.lasInput.directoryName, output_tpu_meta_file), "w")
            outputMetaFile.write(meta_str)
            outputMetaFile.close()

        self.tpu_btn_text.set(u'{} \u2713'.format(self.tpu_btn_text.get()))

    """
    Updates the state of the windRadio, depending on waterSurfaceRadio.
    """
    def updateRadioEnable(self):
        if self.waterSurfaceRadio.selection.get() == 0:
            self.windRadio.setState(tk.DISABLED)
        else:
            self.windRadio.setState(tk.ACTIVE)
    

if __name__ == "__main__":
    Gui()
