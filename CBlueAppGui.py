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
Keana Kief (OSU)
April 29th, 2024

"""
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import time
import json
import os
import subprocess
import webbrowser
from CBlueApp import WIND_OPTIONS, TURBIDITY_OPTIONS, TPU_METRIC_OPTIONS


LICENSE_MSG = \
r"""
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
"""


def show_docs():
    webbrowser.open(r"file://" + os.path.realpath("docs/html/index.html"), new=True)


def show_about():
    about = tk.Toplevel()
    about.resizable(False, False)
    tk.Toplevel.iconbitmap(about, "cBLUE_icon.ico")
    about.wm_title("About cBLUE")
    canvas = tk.Canvas(about, width=615, height=371)
    splash_img = tk.PhotoImage(file="cBLUE_splash.gif", master=canvas)
    canvas.pack(fill="both", expand=True)
    with open("cblue_configuration.json", "r") as f:
        cblue_dict = json.load(f)
    cblue_version = cblue_dict["cBLUE_version"]
    canvas.create_image(0, 0, image=splash_img, anchor="nw")
    canvas_id = canvas.create_text(10, 10, anchor="nw")
    license_msg = f"\n        cBLUE {cblue_version}{LICENSE_MSG}"
    canvas.itemconfig(canvas_id, text=license_msg)
    canvas.itemconfig(canvas_id, font=("arial", 8))
    ttk.Button(about, text="Ok", command=about.destroy).pack()
    about.mainloop()


def get_vdatum_dict():
    vdatum_lookup_path = r"lookup_tables\V_Datum_MCU_Values.txt"
    vdatum_dict = {"---No Region Specified---": 0.0}
    with open(vdatum_lookup_path, "r") as f:
        vdatum_lines = f.readlines()
    vdatum_lines = sorted(vdatum_lines, key=lambda item: item.replace('"', ''))
    for line in vdatum_lines:
        vdatum = line.split("\t")[0].strip().strip('"').replace("\x96", "-")
        mcu = line.split("\t")[-1].strip().strip("\n")
        vdatum_dict[vdatum] = float(mcu)
    return vdatum_dict


def get_sensor_list():
    sensor_json_path = "lidar_sensors.json"
    with open(sensor_json_path, "r") as f:
        sensor_dict = json.load(f)
    sensor_list = list(sensor_dict.keys())
    return sensor_list


def browse(button, var):
    dir_path = filedialog.askdirectory()
    if dir_path:
        var.set(dir_path)
        if "Set" not in button["text"]:
            new_text = button["text"].replace("Choose ", "") + " Set"
            button.config(text=new_text, fg="green")
        print(f'{button["text"]}: {dir_path}')

def set_dir_from_config(dir_path, dir_var, dir_button):
    """Function to set directory paths for the SBET, LAS, and Output directories
    with informatoin from the cblue_configuration.json.
    """
    #If the dir path from the configuration file is not empty and is a valid path to a directory
    #   set the correct directory variable to the directory path and update the button in the GUI
    if(dir_path != "" and os.path.isdir(dir_path)):
        #Update the directory variable
        dir_var.set(dir_path)
        new_text = dir_button["text"].replace("Choose ", "") + " Set"
        dir_button.config(text=new_text, fg="green")
        #Print to the command line that the appropriate directory path has been set    
        print(f'{new_text}: {dir_path}')


def main():
    root = tk.Tk()
    root.wm_title("cBLUE")
    root.iconbitmap(root, "cBLUE_icon.ico")
    root.geometry("325x760")
    norm_font_bold = ("Verdanna", 10, "bold")
    padx = (30, 30)
    pady = (10, 0)

    # Splash screen
    root.withdraw()
    splash = tk.Toplevel()
    splash_img = tk.PhotoImage(file="cBLUE_splash.gif", master=splash)
    splash_label = tk.Label(splash, image=splash_img)
    splash_label.pack()
    root.update()
    time.sleep(1)
    splash.destroy()
    root.deiconify()

    # Menu bar
    menu_bar = tk.Menu(root)
    file_menu = tk.Menu(menu_bar, tearoff=0)
    file_menu.add_command(label="Save settings", command=lambda: start_process(just_save_config=True))
    file_menu.add_separator()
    file_menu.add_command(label="Exit", command=quit)
    menu_bar.add_cascade(label="File", menu=file_menu)
    about_menu = tk.Menu(menu_bar, tearoff=0)
    about_menu.add_command(label="Documentation", command=show_docs)
    about_menu.add_command(label="About", command=show_about)
    menu_bar.add_cascade(label="Help", menu=about_menu)
    root.config(menu=menu_bar)

    #Load settings from cblue_configuration.json
    with open("cblue_configuration.json", "r") as config:
        config_dict = json.load(config)

    # Directory buttons
    dir_frame = tk.Frame(root)
    tk.Label(dir_frame, text="Data Directories", font=norm_font_bold).pack()


    traj_dir_var = tk.StringVar()
    traj_dir_button = tk.Button(dir_frame, text="Choose Trajectory Directory",
                                command=lambda: browse(traj_dir_button, traj_dir_var))
    traj_dir_button.pack(fill="x")
    #If SBET file path is saved in the cblue_configuration.json, set it as the trajectory directory path
    set_dir_from_config(config_dict["directories"]["sbet"], traj_dir_var, traj_dir_button)


    las_dir_var = tk.StringVar()
    las_dir_button = tk.Button(dir_frame, text="Choose LAS Directory",
                               command=lambda: browse(las_dir_button, las_dir_var))
    las_dir_button.pack(fill="x")
    #If las file path is saved in the cblue_configuration.json, set it as the las directory path
    set_dir_from_config(config_dict["directories"]["las"], las_dir_var, las_dir_button)


    out_dir_var = tk.StringVar()
    out_dir_button = tk.Button(dir_frame, text="Choose Output Directory",
                               command=lambda: browse(out_dir_button, out_dir_var))
    out_dir_button.pack(fill="x")
    #If tpu ouput file path is saved in the cblue_configuration.json, set it as the output directory path
    set_dir_from_config(config_dict["directories"]["tpu"], out_dir_var, out_dir_button)

    
    dir_frame.pack(padx=padx, pady=pady, fill="x")

    # Environmental parameters
    def add_tab(options, tab_name, label_text=None):
        """Add tab to Notebook and return Radiobutton variable"""
        tab = ttk.Frame(subaqueous_method_tabs)
        subframe = tk.Frame(tab)
        if label_text:
            tk.Label(subframe, text=label_text).pack(fill="x")
        var = tk.IntVar()
        for n, option in enumerate(options):
            tk.Radiobutton(subframe, text=option, value=n, variable=var, anchor="w").pack(fill="x")
        subframe.pack(fill="x")
        subaqueous_method_tabs.add(tab, text=tab_name)
        return var

    env_frame = tk.Frame(root)
    tk.Label(env_frame, text="Environmental Parameters", font=norm_font_bold).pack()
    subaqueous_method_tabs = ttk.Notebook(env_frame)
    wind_var = add_tab(WIND_OPTIONS, tab_name="Water Surface")
    turbidity_var = add_tab(TURBIDITY_OPTIONS, tab_name="Turbidity")
    subaqueous_method_tabs.pack(fill="x")
    env_frame.pack(padx=padx, pady=pady, fill="x")

    # Water Height
    water_height_frame = tk.Frame(root)
    tk.Label(water_height_frame, text="Water Height", font=norm_font_bold).pack()
    water_height_var = tk.StringVar()
    water_height_var.set(f'{config_dict["water_surface_ellipsoid_height"]:.2f}')
    water_height_msg = "Nominal water surface ellipsoid height (in meters):\nNote: In CONUS locations, this will be "\
                        "a negative\nnumber. Please be sure to enter the negative sign\nbefore the numerical value."
    tk.Label(water_height_frame, text=water_height_msg).pack()
    tk.Entry(water_height_frame, textvariable=water_height_var, justify="center").pack()
    water_height_frame.pack(padx=padx, pady=pady, fill="x")

    # VDatum Region
    vdatum_frame = tk.Frame(root)
    tk.Label(vdatum_frame, text="VDatum Region", font=norm_font_bold).pack()
    vdatum_list = list(get_vdatum_dict().keys())
    vdatum_var = tk.StringVar()
    vdatum_var.set(vdatum_list[0])
    vdatum_om = tk.OptionMenu(vdatum_frame, vdatum_var, *vdatum_list)
    vdatum_om.config(direction="right")
    vdatum_om.pack(fill="x")
    vdatum_frame.pack(padx=padx, pady=pady, fill="x")

    # Sensor Model
    sensor_frame = tk.Frame(root)
    tk.Label(sensor_frame, text="Sensor Model", font=norm_font_bold).pack()
    sensor_var = tk.StringVar()
    tk.OptionMenu(sensor_frame, sensor_var, *get_sensor_list()).pack(fill="x")
    sensor_frame.pack(padx=padx, pady=pady, fill="x")

    # TPU Metric
    tpu_frame = tk.Frame(root)
    tk.Label(tpu_frame, text="TPU Metric", font=norm_font_bold).pack()
    tpu_metric_var = tk.StringVar()
    tk.OptionMenu(tpu_frame, tpu_metric_var, *TPU_METRIC_OPTIONS).pack(fill="x")
    tpu_frame.pack(padx=padx, pady=pady, fill="x")

    # Output Options
    csv_frame = tk.Frame(root)
    tk.Label(csv_frame, text="Output Options", font=norm_font_bold).pack()

    las_var = tk.BooleanVar()
    laz_var = tk.BooleanVar()
    csv_var = tk.BooleanVar()

    ttk.Checkbutton(csv_frame, text = "LAS", variable = las_var, onvalue = True, offvalue = False).pack(padx=20, side=tk.LEFT)
    ttk.Checkbutton(csv_frame, text = "LAZ", variable = laz_var, onvalue = True, offvalue = False).pack(padx=20, side=tk.LEFT)
    ttk.Checkbutton(csv_frame, text = "CSV", variable = csv_var, onvalue = True, offvalue = False).pack(padx=20, side=tk.LEFT)

    # ttk.Radiobutton(csv_frame, text="ExtraBytes LAS", value=False, variable=csv_var).pack(fill="x", padx=padx[-1])
    # ttk.Radiobutton(csv_frame, text="ExtraBytes LAZ", value=False, variable=csv_var).pack(fill="x", padx=padx[-1])
    # ttk.Radiobutton(csv_frame, text="ExtraBytes + CSV", value=True, variable=csv_var).pack(fill="x", padx=padx[-1])
    csv_frame.pack(padx=padx, pady=pady, fill="x")

    def start_process(just_save_config=False):
        """Generate command for CBlueApp.py command line interface. Run the command."""
        # Don't allow saving config if process button is disabled
        if proc_button.cget("state") == "disabled":
            print("Unable to save config. Process button must be active.")
            return
        # Build the command for the command line interface
        vdatum_dict = get_vdatum_dict()
        mcu = vdatum_dict[vdatum_var.get()]
        sensor_integer = get_sensor_list().index(sensor_var.get())
        tpu_integer = TPU_METRIC_OPTIONS.index(tpu_metric_var.get())
        command = ["python",
                   "CBlueApp.py",
                   traj_dir_var.get(),
                   las_dir_var.get(),
                   out_dir_var.get(),
                   str(wind_var.get()),
                   str(turbidity_var.get()),
                   str(mcu),
                   str(sensor_integer),
                   str(tpu_integer),
                   str(water_height_var.get()),
                   "-vdatum_region", vdatum_var.get()
                   ]
        if csv_var.get():
            command.append("--csv")
        if laz_var.get():
            command.append("--laz")
        if just_save_config:
            command.append("--just_save_config")
        print(f"\nCommand: {command}")
        # Run the command
        subprocess.run(command)

    # Process Button
    proc_frame = tk.Frame(root)
    proc_button = tk.Button(proc_frame, text="Process", font=norm_font_bold, command=start_process, state="disabled")
    proc_button.pack(fill="x")
    proc_frame.pack(padx=padx, pady=(pady[0]*2, 0), fill="x")

    def update_process_button(*args):
        """Enable or disable process button based on variable values"""
        disable = False
        # Check that directories exist
        if not os.path.isdir(traj_dir_var.get()):
            disable = True
        if not os.path.isdir(las_dir_var.get()):
            disable = True
        if not os.path.isdir(out_dir_var.get()):
            disable = True
        # Check that sensor and tpu values are selected
        if not sensor_var.get():
            disable = True
        if not tpu_metric_var.get():
            disable = True
        # Check that water height is a valid number
        try:
            float(water_height_var.get())
        except ValueError:
            disable = True
        # Update the button state
        if disable:
            state = "disable"
        else:
            state = "normal"
        proc_button.config(state=state)

    # Check if Process button can be enabled each time one of these vars changes
    traj_dir_var.trace("w", update_process_button)
    las_dir_var.trace("w", update_process_button)
    out_dir_var.trace("w", update_process_button)
    sensor_var.trace("w", update_process_button)
    tpu_metric_var.trace("w", update_process_button)
    water_height_var.trace("w", update_process_button)

    root.mainloop()


if __name__ == "__main__":
    main()
