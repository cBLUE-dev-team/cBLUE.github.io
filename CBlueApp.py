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
101 Kearney Hall
Oregon State University
Corvallis, OR  97331
(541) 737-5688
christopher.parrish@oregonstate.edu

Last Edited By:
Forrest Corcoran (OSU)
3/28/2022

THINGS TO DO:
HOW DOES THIS FILE HAVE NO FRIGGIN COMMENTS?!?!?!
"""

# -*- coding: utf-8 -*-
import logging
import tkinter as tk
from tkinter import ttk
import os
import time
import json
import webbrowser
from code.ControllerPanel import ControllerPanel
from code import license
import code.utils as utils

utils.CustomLogger(filename="CBlue.log")


class CBlueApp(tk.Tk):
    """Gui used to determine the total propagated
    uncertainty of Lidar Topobathymetry measurements.

    Created: 2017-12-0

    @original author: Timothy Kammerer
    @modified by: Nick Forfinski-Sarkozi
    """

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        # print console splash message
        with open(os.path.join("code", "cBLUE_ASCII_splash.txt"), "r") as f:
            message = f.readlines()
            print("".join(message))

        # define configuration file
        self.config_file = "cblue_configuration.json"

        print(
            "Be sure to verify the settings in {}\n"
            "(If you change a setting, restart cBLUE.)\n".format(self.config_file)
        )

        # sets controller_config variables
        self.load_config()

        # show splash screen
        self.withdraw()
        splash = Splash(self)

        tk.Tk.wm_title(self, "cBLUE")
        tk.Tk.iconbitmap(self, "cBLUE_icon.ico")

        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        ### Menu Bar Functions ###
        menubar = tk.Menu(container)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Save settings", command=lambda: self.save_config())
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=quit)
        menubar.add_cascade(label="File", menu=filemenu)

        about_menu = tk.Menu(menubar, tearoff=0)
        about_menu.add_command(label="Documentation", command=self.show_docs)
        about_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=about_menu)

        tk.Tk.config(self, menu=menubar)

        self.frames = {}
        for F in (ControllerPanel,):  # makes it easy to add "pages" in future
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(ControllerPanel)

        # after splash screen, show main GUI
        time.sleep(1)
        splash.destroy()
        self.deiconify()

    def load_config(self):
        if os.path.isfile(self.config_file):
            with open(self.config_file) as cf:
                self.controller_config = json.load(cf)
        else:
            logging.cblue("configuration file doesn't exist")

    def save_config(self):
        with open(self.config_file, "w") as fp:
            json.dump(self.controller_config, fp)

    def show_docs(self):
        webbrowser.open(r"file://" + os.path.realpath("docs/html/index.html"), new=True)

    def show_about(self):
        about = tk.Toplevel()
        about.resizable(False, False)
        tk.Toplevel.iconbitmap(about, "cBLUE_icon.ico")
        about.wm_title("About cBLUE")

        canvas = tk.Canvas(about, width=615, height=371)
        splash_img = tk.PhotoImage(file="cBLUE_splash.gif", master=canvas)
        canvas.pack(fill="both", expand="yes")

        license_msg = license.format(self.controller_config["cBLUE_version"])

        canvas.create_image(0, 0, image=splash_img, anchor=tk.NW)
        canvas_id = canvas.create_text(10, 10, anchor="nw")
        canvas.itemconfig(canvas_id, text=license_msg)
        canvas.itemconfig(canvas_id, font=("arial", 8))

        # label = tk.Label(about, image=splash_img, text=license_msg, compound=tk.CENTER)
        # label.pack()
        b1 = ttk.Button(about, text="Ok", command=about.destroy)
        b1.pack()
        about.mainloop()

    @staticmethod
    def popupmsg(msg):
        popup = tk.Tk()
        popup.wm_title("!")
        label = ttk.Label(popup, text=msg, font=NORM_FONT)
        label.pack(side="top", fill="x", pady=10)
        b1 = ttk.Button(popup, text="Ok", command=popup.destroy)
        b1.pack()
        popup.mainloop()

    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()


class Splash(tk.Toplevel):
    def __init__(self, parent):
        tk.Toplevel.__init__(self, parent)
        impath = os.path.join("images", "cBLUE_splash.gif")
        splash_img = tk.PhotoImage(file=impath, master=self)
        label = tk.Label(self, image=splash_img)
        label.pack()
        self.update()


if __name__ == "__main__":

    app = CBlueApp()
    app.geometry("350x650")
    app.mainloop()
