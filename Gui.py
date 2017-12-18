# -*- coding: utf-8 -*-
# Import Statements
import Tkinter as tk
import os
import numpy as np
import webbrowser

# Import Gui helper classes
from DirectorySelectButton import DirectorySelectButton
from RadioFrame import RadioFrame

# Import Processing code
import pre_TPU_tile_processing
import calc_aerial_TPU
import SubAqueous

"""
Gui used to determine the total propagated uncertainty of Lidar Topobathymetry measurements.

Created: 2017-12-07

@author: Timothy Kammerer
"""

class Gui:
    
    instance = None
    
    #%% Initialization
    """
    Initializes the Gui.
    """
    def __init__(self):
        Gui.instance = self
        self.root = tk.Tk(className = " GUI_topobathy_list")
        self.lastFileLoc = os.getcwd()
        
        # Build the title label
        self.title = tk.Label(text = "RIEGL VQ-880-G\nTOTAL PROPAGATED\nUNCERTAINTY(TPU) PROGRAM", background = "green")
        self.title.grid(row = 0, sticky = tk.EW)
        
        #  Build the interface
        self.buildInput()
        self.buildProcessButtons()
        
        #  Make the window non-resizable
        self.root.resizable(width = False, height = False)
        
        # mainloop
        self.root.mainloop()
    
    #%% GUI Building
    """
    Builds the input for the Gui.
    """
    def buildInput(self):
        self.buildSubaerialInput()
        self.buildSubaqueousInput()
    
    """
    Builds the directory selection input and processing Buttons for the subaerial portion.
    """
    def buildSubaerialInput(self):
        # Create Frame
        frame = tk.Frame(self.root, borderwidth = 2, relief = tk.GROOVE)
        frame.grid(row = 1)
        
        #Create Frame Label
        tk.Label(frame, text = "SUB-AERIAL TPU").grid(row = 0, columnspan = 3, sticky = tk.EW)
        
        # Create variable to measure progress through button stages
        self.buttonEnableStage = 0
        
        # Create Directory Inputs
        buttonWidth = 45
        
        self.lasInput = DirectorySelectButton(self, frame, "LAS",
                                              buttonWidth, callback = self.updateButtonEnable)
        self.lasInput.grid(row = 1, column = 0)
        self.lasSplitTileInput = DirectorySelectButton(self, frame, "LAS SPLIT TILE", buttonWidth,
                                                       callback = self.updateButtonEnable)
        self.lasSplitTileInput.grid(row = 1, column = 1)
        self.sbetInput = DirectorySelectButton(self, frame, "SBET", buttonWidth,
                                               callback = self.updateButtonEnable)
        self.sbetInput.grid(row = 1, column = 2)
        
        self.lasSplitTileInput.setState(tk.DISABLED)
        self.sbetInput.setState(tk.DISABLED)
        
        # Create Processing Buttons
        self.lasProcess = tk.Button(frame, text = "Pre-Process Tiles", width = buttonWidth,
                                    height = 2, state = tk.DISABLED, command = self.lasProcessCallback)
        self.lasProcess.grid(row = 2, column = 0)
        self.subAerialProcess = tk.Button(frame, text = "Process Sub-Aerial TPU", width = buttonWidth,
                                          height = 2, state = tk.DISABLED, command = self.subAerialProcessCallback)
        self.subAerialProcess.grid(row = 2, column = 1)
    
    """
    Builds the radio button input for the subaqueous portion.
    """
    def buildSubaqueousInput(self):
        # Create Frame
        frame = tk.Frame(self.root, borderwidth = 2, relief = tk.GROOVE)
        frame.grid(row = 2, sticky = tk.NSEW)
        
        # Create Frame Label
        tk.Label(frame, text = "SUB-AQUEOUS TPU").grid(row = 0, columnspan = 3, sticky = tk.EW)
        
        # Create Radio Buttons
        frameWidth = 45
        
        waterSurfaceOptions = ["Riegl VQ-880-G", "Model(ECKV spectrum)"]
        windOptions = ["Calm-Light air (0-3 knots)", "Light breeze (3-6 knots)", "Gentle Breeze (6-10 knots)",
                       "Moderate Breeze (10-15 knots)", "Fresh Breeze (15-20 knots)"]
        turbidityOptions = ["Clear", "Clear-Moderate", "Moderate", "Moderate-High", "High"]
        
        self.waterSurfaceRadio = RadioFrame(frame, "Water Surface", waterSurfaceOptions, 1, callback = self.updateRadioEnable, width = frameWidth)
        self.waterSurfaceRadio.grid(row = 1, column = 0, sticky = tk.N)
        self.windRadio = RadioFrame(frame, "Wind", windOptions, 1, width = frameWidth)
        self.windRadio.grid(row = 1, column = 1, sticky = tk.N)
        self.turbidityRadio = RadioFrame(frame, "Turbidity", turbidityOptions, 0, width = frameWidth)
        self.turbidityRadio.grid(row = 1, column = 2, sticky = tk.N)
        
    """
    Builds the radio button input for the subaqueous portion.
    """
    def buildProcessButtons(self):
        frame = tk.Frame(self.root)
        frame.grid(row = 3, sticky = tk.W)
        
        buttonWidth = 30
        
        self.tpuProcess = tk.Button(frame, text = "Process TPU", width = buttonWidth, height = 2,
                                    state = tk.DISABLED, command = self.tpuProcessCallback)
        self.tpuProcess.grid(row = 0, column = 0)
        self.openOutput = tk.Button(frame, text = "Open output file", width = buttonWidth, height = 2,
                                    state = tk.DISABLED, command = self.openOutputCallback)
        self.openOutput.grid(row = 0, column = 1)
    
    #%% Button Callbacks
    
    """
    Updates to enable buttons in order:
        - Select LAS Directory
        - Generate LAS Tiles
        - Slect LAS SPLIT TILE directory and Select SBET directory
        - Process TPU Sub-aerial
        - Process TPU
        - Open Output File
    """
    def updateButtonEnable(self, newValue = None):
        if newValue == None:
            if self.buttonEnableStage == 0:
                if self.lasInput.directoryName == "":
                    return
                self.buttonEnableStage = 1
            elif self.buttonEnableStage == 2:
                if self.lasSplitTileInput.directoryName == "" or self.sbetInput.directoryName == "":
                    return
                self.buttonEnableStage = 3
            else:
                return
        else:
            self.buttonEnableStage = newValue
        
        if self.buttonEnableStage == 1:
            self.lasProcess.config(state = tk.ACTIVE)
        elif self.buttonEnableStage == 2:
            self.lasSplitTileInput.setState(tk.ACTIVE)
            self.sbetInput.setState(state = tk.ACTIVE)
        elif self.buttonEnableStage == 3:
            self.subAerialProcess.config(state = tk.ACTIVE)
        elif self.buttonEnableStage == 4:
            self.tpuProcess.config(state = tk.ACTIVE)
        elif self.buttonEnableStage == 5:
            self.openOutput.config(state = tk.ACTIVE)
        
    """
    Callback for the lasProcess button.
    """
    def lasProcessCallback(self):
        pre_TPU_tile_processing.main(self.lasInput.directoryName)
        self.updateButtonEnable(2)
        
    """
    Callback for the subAerialProcess button.
    """
    def subAerialProcessCallback(self):
        self.LE_post = calc_aerial_TPU.main(self.sbetInput.directoryName, self.lasSplitTileInput.directoryName)
        self.updateButtonEnable(4)
        
    """
    Callback for processing the subaqueous data and inputs and creating outputs.
    """
    def tpuProcessCallback(self):
        windSelect = self.windRadio.selection.get()
        kdSelect = self.turbidityRadio.selection.get()
        # Get the wind value from the GUI
        if(windSelect == 0):
            wind = [1]
        elif(windSelect == 1):
            wind = [2, 3]
        elif(windSelect == 2):
            wind = [4, 5]
        elif(windSelect == 3):
            wind = [6, 7, 8]
        elif(windSelect == 4):
            wind = [9, 10]
        # Get the Kd value from the GUI
        if(kdSelect == 0):
            kd = list(range(5, 11))
        elif(kdSelect == 1):
            kd = list(range(11, 18))
        elif(kdSelect == 2):
            kd = list(range(18, 26))
        elif(kdSelect == 3):
            kd = list(range(26, 33))
        elif(kdSelect == 4):
            kd = list(range(33, 41))
        depth = self.LE_post[:, 2] + 23
        res = SubAqueous.main(self.waterSurfaceRadio.selection.get(), wind, kd, depth)
        sigma = list()
        outputFile = open("{}\\{}".format(self.lasInput.directoryName, "result.csv"), "w")
        for n in range(len(res)):
            sigma.append(np.sqrt(res[n]**2+self.LE_post[n, 5]**2))
            outputFile.write("{},{},{},{},{},{}\n".format(round(self.LE_post[n, 0], 5), round(self.LE_post[n, 1], 5),
                             round(self.LE_post[n, 2], 3), round(self.LE_post[n, 5], 3), round(res[n], 3), round(sigma[n], 3)))
        outputFile.close()
        
        self.updateButtonEnable(5)
        
    """
    Callback for opening the output file in notepad.
    """
    def openOutputCallback(self):
        webbrowser.open("{}\\{}".format(self.lasInput.directoryName, "result.csv"))
        self.updateButtonEnable(6)
        
    """
    Updates the state of the windRadio, depending on waterSurfaceRadio.
    """
    def updateRadioEnable(self):
        if self.waterSurfaceRadio.selection.get() == 0:
            self.windRadio.setState(tk.DISABLED)
        else:
            self.windRadio.setState(tk.ACTIVE)
    
    #%%
if __name__ == "__main__":
    Gui()