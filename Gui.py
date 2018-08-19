# -*- coding: utf-8 -*-
# Import Statements

import logging
logging.basicConfig(format='%(asctime)s:%(message)s', level=logging.INFO)

import Tkinter as tk
import os
import numpy as np
import numexpr as ne  # used to speed up numpy calculations
# import webbrowser
import pandas as pd

# Import Gui helper classes
from DirectorySelectButton import DirectorySelectButton
from RadioFrame import RadioFrame

import pathos.pools as pp  # for multiprocessing of las files

# Import Processing code
from Sbet import Sbet
from Las import Las
from Merge import Merge
from Subaerial import Subaerial
from Subaqueous import Subaqueous
from Datum import Datum
from Tpu import Tpu

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

        #  Build the interface
        self.buildInput()
        self.buildProcessButtons()
        
        #  Make the window non-resizable
        self.root.resizable(width=False, height=False)
        
        # mainloop
        self.root.mainloop()
    
    # GUI Building
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
        frame = tk.Frame(self.root, borderwidth=2, relief=tk.GROOVE)
        frame.grid(row=1)
        
        #Create Frame Label
        tk.Label(frame, text="Data Directories", font='Helvetica 10 bold').grid(row=0, columnspan=3, sticky=tk.EW)
        
        # Create variable to measure progress through button stages
        self.buttonEnableStage = 0
        
        # Create Directory Inputs
        buttonWidth = 82
        buttonHeight = 1

        self.sbetInput = DirectorySelectButton(self, frame, "SBET FILES", buttonWidth,
                                               buttonHeight, callback=self.updateButtonEnable)
        self.sbetInput.grid(row=2, column=0)

        self.lasInput = DirectorySelectButton(self, frame, "ORIGINAL LAS TILES", buttonWidth,
                                              buttonHeight, callback=self.updateButtonEnable)
        self.lasInput.grid(row=3, column=0)

        self.tpuOutput = DirectorySelectButton(self, frame, "OUTPUT FILES", buttonWidth,
                                               buttonHeight, callback=self.updateButtonEnable)
        self.tpuOutput.grid(row=4, column=0)
        
    """
    Builds the radio button input for the subaqueous portion.
    """
    def buildParametersInput(self):
        # Create Frame
        parameters_frame = tk.Frame(
            self.root,
            borderwidth=2,
            relief=tk.GROOVE)
        parameters_frame.grid(row=2, sticky=tk.NSEW)

        # Create Frame Label
        tk.Label(parameters_frame,
                 text="SUB-AQUEOUS Parameters",
                 font='Helvetica 10 bold').grid(row=0,
                                                columnspan=2,
                                                sticky=tk.EW)

        water_surface_subframe = tk.Frame(parameters_frame, borderwidth=2, relief=tk.GROOVE)
        water_surface_subframe.grid(row=1, column=0)

        turbidity_subframe = tk.Frame(parameters_frame, borderwidth=2, relief=tk.GROOVE)
        turbidity_subframe.grid(row=1, column=1, sticky=(tk.N, tk.W, tk.E, tk.S))
        turbidity_subframe.columnconfigure(0, weight=1)
        turbidity_subframe.rowconfigure(0, weight=1)

        tk.Label(parameters_frame,
                 text="Regional VDatum Maximum Cumulative Uncertainty (MCU)",
                 font='Helvetica 10 bold').grid(row=2, columnspan=2, sticky=tk.EW)
        datum_transform_subframe = tk.Frame(parameters_frame, borderwidth=2, relief=tk.GROOVE)
        datum_transform_subframe.grid(row=3, column=0, columnspan=2, sticky=tk.EW)
        datum_transform_subframe.columnconfigure(0, weight=1)
        datum_transform_subframe.rowconfigure(0, weight=1)

        # Create Radio Buttons
        frameWidth = 40

        self.waterSurfaceOptions = [
            "Riegl VQ-880-G",
            "Model (ECKV spectrum)"]

        self.windOptions = [w[0] for w in self.wind_vals.values()]
        self.turbidityOptions = [k[0] for k in self.kd_vals.values()]

        self.waterSurfaceRadio = RadioFrame(water_surface_subframe, "Water Surface", self.waterSurfaceOptions,
                                            1, callback=self.updateRadioEnable, width=frameWidth)
        self.waterSurfaceRadio.grid(row=0, column=0, columnspan=2, sticky=tk.W)

        self.windRadio = RadioFrame(water_surface_subframe, None, self.windOptions, 1, width=frameWidth)
        self.windRadio.grid(row=1, column=1, sticky=tk.W)

        self.turbidityRadio = RadioFrame(turbidity_subframe, "Turbidity", self.turbidityOptions, 0, width=frameWidth)
        self.turbidityRadio.grid(row=0, column=0, sticky=tk.N)
        # List with options

        tk.Label(datum_transform_subframe, text="VDatum Region").grid(row=0, column=0, sticky=tk.EW)

        regions, mcu_values, default_msg = Datum.get_vdatum_region_mcus()
        self.vdatum_regions = dict({(key, value) for (key, value) in zip(regions, mcu_values)})
        self.vdatum_regions.update({default_msg: 0})

        self.tkvar = tk.StringVar()
        self.tkvar.set(default_msg)  # set the default option
        self.vdatum_region_option_menu = tk.OptionMenu(
            datum_transform_subframe,
            self.tkvar,
            *sorted(self.vdatum_regions.keys()),
            command=self.updateVdatumMcuValue)
        self.vdatum_region_option_menu.config(width=60)
        self.vdatum_region_option_menu.grid(row=0, column=1)

    """
    Builds the process buttons.
    """
    def buildProcessButtons(self):
        self.isSbetLoaded = False

        frame = tk.Frame(self.root, borderwidth=2, relief=tk.GROOVE)
        frame.grid(row=3, sticky=tk.S)

        # Create Frame Label
        tk.Label(frame, text='Process Buttons', font='Helvetica 10 bold').grid(row=0, columnspan=3, sticky=tk.EW)

        buttonWidth = 26
        buttonHeight = 3

        self.sbet_btn_text = tk.StringVar()
        self.sbet_btn_text.set("Load SBET Files")
        self.sbetProcess = tk.Button(frame, textvariable=self.sbet_btn_text, width=buttonWidth,
                                     height=buttonHeight, state=tk.DISABLED, command=self.sbetProcessCallback)
        self.sbetProcess.grid(row=1, column=1)

        self.tpu_btn_text = tk.StringVar()
        self.tpu_btn_text.set("Process TPU")
        self.tpuProcess = tk.Button(frame,
                                    textvariable=self.tpu_btn_text,
                                    width=buttonWidth,
                                    height=buttonHeight,
                                    state=tk.DISABLED,
                                    command=self.tpuProcessCallback)
        self.tpuProcess.grid(row=1, column=2)

    # Button Callbacks
    def updateVdatumMcuValue(self, region):
        logging.info(self.tkvar.get())
        self.mcu = self.vdatum_regions[region]
        logging.info('The MCU for {} is {} cm.'.format(region, self.mcu))

    def updateButtonEnable(self, newValue=None):
        if newValue == None:
            if self.sbetInput.directoryName != "":
                self.sbetProcess.config(state=tk.ACTIVE)
            if self.tpuOutput.directoryName != "" and self.isSbetLoaded:
                self.tpuProcess.config(state=tk.ACTIVE)
        else:
            self.buttonEnableStage = newValue

    """
    Callback for the sbetProcess button.
    """
    def sbetProcessCallback(self):
        self.sbet = Sbet(self.sbetInput.directoryName)
        self.isSbetLoaded = True
        self.sbet_btn_text.set(u'{} \u2713'.format(self.sbet_btn_text.get()))
        self.updateButtonEnable()

    """
    Callback for processing tpu and creating outputs.
    """
    def tpuProcessCallback(self):
        surface_ind = self.waterSurfaceRadio.selection.get()
        surface_selection = self.waterSurfaceOptions[surface_ind]

        wind_ind = self.windRadio.selection.get()
        wind_selection = self.windOptions[wind_ind]

        kd_ind = self.turbidityRadio.selection.get()
        kd_selection = self.turbidityOptions[kd_ind]

        tpu = Tpu(
            self.sbet_df,
            surface_selection,
            surface_ind,
            wind_selection,
            self.wind_vals[wind_ind][1],
            kd_selection,
            self.kd_vals[kd_ind][1],
            self.vdatum_regions[self.tkvar.get()],
            self.mcu,
            self.tpuOutput.directoryName)

        las_files = [os.path.join(self.lasInput.directoryName, l)
                     for l in os.listdir(self.lasInput.directoryName)
                     if l.endswith('.las')]
        tpu.run_tpu_multiprocessing(las_files)

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
