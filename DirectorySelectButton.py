# -*- coding: utf-8 -*-
import tkFileDialog
import os
from Tkinter import Button

"""
Button used to get the name of a directing containing files that need to be imported during processing.

Created: 2017-12-07

@author Timothy Kammerer
"""
class DirectorySelectButton(object):

    """
    Initializes the DirectorySelectButton.
    
    @param   fileType    string
    @param   openTypes   string[]
    """
    def __init__(self, master, frame, directType, width, height, callback=None):
        self.master = master
        self.directType = directType
        self.width = width
        self.height = height
        self.button = Button(
            frame,
            text="Choose {} Directory".format(self.directType),
            command=self.callback,
            width=width,
            height=self.height)
        self.directoryName = ""
        self.extraCallback = callback
    
    """
    Wrapper function for self.button.grid.
    """
    def grid(self, **args):
        self.button.grid(**args)
    
    """
    Sets the state of the button.
    """
    def setState(self, state):
        self.button.config(state = state)

    """
    Callback for the button.
    
    Gets the directoryName from user with tkFileDialog.
    Updates the display to reflect directory choice.
    """
    def callback(self):
        directoryName = tkFileDialog.askdirectory(
            initialdir=self.master.lastFileLoc,
            title="Select {} File".format(self.directType))

        if directoryName == "":
            return

        self.directoryName = os.path.normpath(directoryName)
        self.master.lastFileLoc = self.directoryName
        
        #update the Gui
        displayDirectory = self.directoryName
        
        self.button.config(
            text="{}: {}".format(self.directType, displayDirectory),
            anchor='w')
        
        if self.extraCallback != None:
            self.extraCallback()
