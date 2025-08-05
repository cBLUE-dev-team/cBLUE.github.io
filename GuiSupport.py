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
August 4th, 2025

"""

# -*- coding: utf-8 -*-
from tkinter import filedialog, Button, IntVar, Radiobutton, Frame, Label, W


class DirectorySelectButton(object):
    """Button used to get the name of a directing containing
    files that need to be imported during processing.

    Created: 2017-12-07

    @author Timothy Kammerer
    """

    def __init__(self, master, frame, direct_type, dir_path, width, callback=None):
        """Initializes the DirectorySelectButton.

        @param   fileType    string
        @param   openTypes   string[]
        """

        self.master = master
        self.directType = direct_type
        self.width = width
        self.button = Button(
            frame,
            text="Choose {} Directory".format(self.directType),
            command=self.callback,
            width=width,
        )
        self.directoryName = dir_path
        self.extraCallback = callback

    def grid(self, **args):
        """Wrapper function for self.button.grid."""

        self.button.grid(**args)

    def set_state(self, state):
        """Sets the state of the button."""

        self.button.config(state=state)

    def callback(self):
        """Callback for the button.

        Gets the directoryName from user with filedialog.
        Updates the display to reflect directory choice.
        """

        directoryName = filedialog.askdirectory(
            initialdir=self.master.lastFileLoc,
            title="Select {} File".format(self.directType),
        )

        if directoryName == "":
            return

        self.directoryName = directoryName
        self.master.lastFileLoc = self.directoryName

        # update the Gui
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
            text="{} Directory Set".format(self.directType), fg="darkgreen"
        )

        if self.extraCallback is not None:
            self.extraCallback()


class RadioFrame:
    """Created: 2017-12-08

    @author: Timothy Kammerer
    """

    def __init__(
        self,
        root,
        radioName,
        radioOptions,
        startSelect=0,
        background=None,
        foreground=None,
        callback=None,
        width=40,
    ):
        self.frame = Frame(root, background=background)

        if radioName != None:
            Label(
                self.frame,
                text=radioName,
                width=width,
                background=background,
                foreground=foreground,
            ).grid(row=0)

        self.selection = IntVar(self.frame)
        self.buttons = list()

        for i, opt in enumerate(radioOptions):
            self.buttons.append(
                Radiobutton(
                    self.frame,
                    text=opt,
                    variable=self.selection,
                    value=i,
                    command=callback,
                    background=background,
                    activebackground=background,
                    foreground=foreground,
                    activeforeground=foreground,
                )
            )
            self.buttons[i].grid(row=i + 1, sticky=W)
        self.buttons[startSelect].select()

    def grid(self, **options):
        self.frame.grid(**options)

    def setState(self, state):
        for button in self.buttons:
            button.config(state=state)


if __name__ == "__main__":
    pass
# dummy comment
