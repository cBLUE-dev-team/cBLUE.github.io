# -*- coding: utf-8 -*-
import tkFileDialog
import os
from Tkinter import Button


class DirectorySelectButton(object):
    """Button used to get the name of a directing containing files that need to be imported during processing.

    Created: 2017-12-07

    @author Timothy Kammerer
    """

    def __init__(self, master, frame, directType, width, callback=None):
        """Initializes the DirectorySelectButton.

        @param   fileType    string
        @param   openTypes   string[]
        """

        self.master = master
        self.directType = directType
        self.width = width
        self.button = Button(
            frame,
            text="Choose {} Directory".format(self.directType),
            command=self.callback,
            width=width)
        self.directoryName = ""
        self.extraCallback = callback

    def grid(self, **args):
        """Wrapper function for self.button.grid."""

        self.button.grid(**args)
    
    def set_state(self, state):
        """Sets the state of the button."""

        self.button.config(state=state)

    def callback(self):
        """Callback for the button.

        Gets the directoryName from user with tkFileDialog.
        Updates the display to reflect directory choice.
        """

        directoryName = tkFileDialog.askdirectory(
            initialdir=self.master.lastFileLoc,
            title="Select {} File".format(self.directType))

        if directoryName == "":
            return

        self.directoryName = directoryName
        self.master.lastFileLoc = self.directoryName
        
        #update the Gui
        directoryRoots = self.directoryName.split("/")
        displayDirectory = str()

        while len(directoryRoots) != 0:
            currentLine = directoryRoots.pop(0)

            if len(directoryRoots) != 0:
                while len(currentLine) + len(directoryRoots[0]) < self.width:
                    currentLine = "{}\\{}".format(currentLine, directoryRoots.pop(0))

                    if len(directoryRoots) == 0:
                        break
            
            displayDirectory = "{}{}".format(displayDirectory, currentLine)
        
        self.button.config(
            text="{} Directory Set".format(self.directType), fg='darkgreen')
        
        if self.extraCallback != None:
            self.extraCallback()


if __name__ == '__main__':
    print(DirectorySelectButton.__doc__)
