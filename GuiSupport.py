# -*- coding: utf-8 -*-
import tkFileDialog
from Tkinter import Button, IntVar, Radiobutton, Frame, Label, GROOVE, W


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
            text='Choose {} Directory'.format(self.directType),
            command=self.callback,
            width=width)
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

        Gets the directoryName from user with tkFileDialog.
        Updates the display to reflect directory choice.
        """

        directoryName = tkFileDialog.askdirectory(
            initialdir=self.master.lastFileLoc,
            title="Select {} File".format(self.directType))

        if directoryName == '':
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
        
        self.button.config(text="{} Directory Set".format(self.directType), fg='darkgreen')
        
        if self.extraCallback is not None:
            self.extraCallback()


class RadioFrame:
    """Created: 2017-12-08

    @author: Timothy Kammerer
    """

    def __init__(self, root, radioName, radioOptions,
                 startSelect=0, background=None, foreground=None,
                 callback=None, width=40):
        self.frame = Frame(root, background=background)

        if radioName != None:
            Label(
                self.frame,
                text=radioName,
                width=width,
                background=background,
                foreground=foreground).grid(row=0)

        self.selection = IntVar(self.frame)
        self.buttons = list()

        for i, opt in enumerate(radioOptions):
            self.buttons.append(Radiobutton(
                self.frame,
                text=opt,
                variable=self.selection,
                value=i,
                command=callback,
                background=background,
                activebackground=background,
                foreground=foreground,
                activeforeground=foreground))
            self.buttons[i].grid(row=i + 1, sticky=W)
        self.buttons[startSelect].select()

    def grid(self, **options):
        self.frame.grid(**options)

    def setState(self, state):
        for button in self.buttons:
            button.config(state=state)


if __name__ == '__main__':
    print(DirectorySelectButton.__doc__)
