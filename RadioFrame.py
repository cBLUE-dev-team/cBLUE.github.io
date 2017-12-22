# -*- coding: utf-8 -*-
from Tkinter import IntVar, Radiobutton, Frame, Label, GROOVE, W

"""
Created: 2017-12-08

@author: Timothy Kammerer
"""

class RadioFrame:
    def __init__(
            self,
            root,
            radioName,
            radioOptions,
            startSelect=0,
            background=None,
            foreground=None,
            callback=None,
            width=40):
        self.frame = Frame(
            root,
            borderwidth=0,
            relief=GROOVE,
            background=background)

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
            self.buttons[i].grid(row=i+1, sticky=W)
        self.buttons[startSelect].select()
    
    def grid(self, **options):
        self.frame.grid(**options)
    
    def setState(self, state):
        for button in self.buttons:
            button.config(state = state)