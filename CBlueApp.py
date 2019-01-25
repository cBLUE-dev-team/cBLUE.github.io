# -*- coding: utf-8 -*-
import logging
logging.basicConfig(format='%(asctime)s:%(message)s', level=logging.INFO)

import Tkinter as tk
import ttk
import os
import time
import json

# Import Gui helper classes
from GuiSupport import DirectorySelectButton, RadioFrame

from Sbet import Sbet
from Datum import Datum
from Tpu import Tpu

import matplotlib
matplotlib.use('Agg')
from matplotlib import style
from matplotlib import pyplot as plt


LARGE_FONT = ('Verdanna', 12)
NORM_FONT = ('Verdanna', 10)
NORM_FONT_BOLD = ('Verdanna', 10, 'bold')
SMALL_FONT = ('Verdanna', 8)

style.use('ggplot')  # 'dark_background'

f = plt.figure()


class CBlueApp(tk.Tk):
    """ Gui used to determine the total propagated
    uncertainty of Lidar Topobathymetry measurements.

    Created: 2017-12-07

    @original author: Timothy Kammerer
    @modified by: Nick Forfinski-Sarkozi
    """

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        self.config_file = 'cblue_configuration.json'
        self.load_config()

        # show splash screen
        self.withdraw()
        splash = Splash(self)

        tk.Tk.wm_title(self, 'cBLUE')
        tk.Tk.iconbitmap(self, 'cBLUE_icon.ico')

        container = tk.Frame(self)
        container.pack(side='top', fill='both', expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        menubar = tk.Menu(container)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label='Save settings',
                             command=lambda: self.save_config())
        filemenu.add_separator()
        filemenu.add_command(label='exit', command=quit)
        menubar.add_cascade(label='File', menu=filemenu)

        exchangeChoice = tk.Menu(menubar, tearoff=0)
        exchangeChoice.add_command(label='Lidar System',
                                   command=lambda: self.popupmsg('not supported yet...'))
        exchangeChoice.add_command(label='Properties',
                                   command=lambda: self.popupmsg('not supported yet...'))
        # menubar.add_cascade(label='Edit', menu=exchangeChoice)

        exchangeChoice = tk.Menu(menubar, tearoff=0)
        exchangeChoice.add_command(label='Map Window',
                                   command=lambda: self.build_map_panel)
        exchangeChoice.add_command(label='Graph Window',
                                   command=lambda: self.popupmsg('not supported yet...'))
        exchangeChoice.add_command(label='Table Window',
                                   command=lambda: self.popupmsg('not supported yet...'))
        # menubar.add_cascade(label='Display', menu=exchangeChoice)

        exchangeChoice = tk.Menu(menubar, tearoff=0)
        exchangeChoice.add_command(label='About', command=self.show_about)
        menubar.add_cascade(label='Help', menu=exchangeChoice)

        tk.Tk.config(self, menu=menubar)

        self.frames = {}
        for F in (ControllerPanel,):  # makes it easy to add "pages" in future
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky='nsew')

        self.show_frame(ControllerPanel)

        # after splash screen, show main GUI
        time.sleep(1)
        splash.destroy()
        self.deiconify()

    def load_config(self):
        if os.path.isfile(self.config_file):
            with open(self.config_file) as cf:
                self.controller_configuration = json.load(cf)
        else:
            logging.info("configuration file doesn't exist")

    def save_config(self):
        config = 'cblue_configuration.json'
        print('saving {}...\n{}'.format(config, self.controller_configuration))
        with open(config, 'w') as fp:
            json.dump(self.controller_configuration, fp)

    @staticmethod
    def show_about():
        about = tk.Toplevel()
        tk.Toplevel.iconbitmap(about, 'cBLUE_icon.ico')
        about.wm_title('About cBLUE')
        splash_img = tk.PhotoImage(file='cBLUE_splash.gif')
        label = tk.Label(about, image=splash_img)
        label.pack()
        b1 = ttk.Button(about, text='Ok', command=about.destroy)
        b1.pack()
        about.mainloop()

    @staticmethod
    def popupmsg(msg):
        popup = tk.Tk()
        popup.wm_title('!')
        label = ttk.Label(popup, text=msg, font=NORM_FONT)
        label.pack(side='top', fill='x', pady=10)
        b1 = ttk.Button(popup, text='Ok', command=popup.destroy)
        b1.pack()
        popup.mainloop()

    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()


class Splash(tk.Toplevel):
    def __init__(self, parent):
        tk.Toplevel.__init__(self, parent)
        splash_img = tk.PhotoImage(file='cBLUE_splash.gif', master=self)
        label = tk.Label(self, image=splash_img)
        label.pack()
        self.update()


class ControllerPanel(ttk.Frame):

    def __init__(self, parent, controller):
        ttk.Frame.__init__(self, parent)

        self.lastFileLoc = os.getcwd()

        # Build the title label
        self.title = tk.Label(self, text="RIEGL VQ-880-G\n"
                                         "TOTAL PROPAGATED UNCERTAINTY (TPU) PROGRAM\n"
                                         "v2.0", background="green")

        # TODO:  get from separate text file
        self.kd_vals = {0: ('Clear', range(6, 11)),
                        1: ('Clear-Moderate', range(11, 18)),
                        2: ('Moderate', range(18, 26)),
                        3: ('Moderate-High', range(26, 33)),
                        4: ('High', range(33, 37))}

        # TODO:  get from separate text file
        self.wind_vals = {0: ('Calm-light air (0-2 kts)', [1]),
                          1: ('Light Breeze (3-6 kts)', [2, 3]),
                          2: ('Gentle Breeze (7-10 kts)', [4, 5]),
                          3: ('Moderate Breeze (11-15 kts)', [6, 7]),
                          4: ('Fresh Breeze (16-20 kts)', [8, 9, 10])}

        self.is_sbet_dir_set = False
        self.is_las_dir_set = False
        self.is_tpu_dir_set = False
        self.is_sbet_loaded = False
        self.is_tpu_computed = False
        self.buttonEnableStage = 0  # to measure progress through button stages
        self.sbetInput = None
        self.lasInput = None
        self.tpuOutput = None
        self.sbet = None
        self.parent = parent
        self.controller = controller

        #  Build the control panel
        self.control_panel_width = 30
        self.build_control_panel()
        # self.build_map_panel()

    def build_control_panel(self):
        self.controller_panel = ttk.Frame(self)
        self.controller_panel.grid(row=0, column=0, sticky=tk.EW)
        self.controller_panel.grid_rowconfigure(0, weight=1)
        self.build_directories_input()
        self.build_subaqueous_input()
        self.build_vdatum_input()
        self.build_process_buttons()
        self.update_button_enable()

    def build_directories_input(self):
        """Builds the directory selection input and processing Buttons for the subaerial portion."""

        subaerial_frame = tk.Frame(self.controller_panel)
        subaerial_frame.grid(row=0)
        subaerial_frame.columnconfigure(0, weight=1)
        label = tk.Label(subaerial_frame, text="Data Directories", font=NORM_FONT_BOLD)
        label.grid(row=0, columnspan=1, pady=(10, 0), sticky=tk.EW)

        self.sbetInput = DirectorySelectButton(
            self, subaerial_frame, "Trajectory",
            self.controller.controller_configuration['directories']['sbet'],
            self.control_panel_width,
            callback=self.update_button_enable)
        self.sbetInput.grid(row=1, column=0)

        self.lasInput = DirectorySelectButton(
            self, subaerial_frame, "LAS",
            self.controller.controller_configuration['directories']['las'],
            self.control_panel_width,
            callback=self.update_button_enable)
        self.lasInput.grid(row=2, column=0)

        self.tpuOutput = DirectorySelectButton(
            self, subaerial_frame, "Output",
            self.controller.controller_configuration['directories']['tpu'],
            self.control_panel_width,
            callback=self.update_button_enable)
        self.tpuOutput.grid(row=3, column=0)

    def build_subaqueous_input(self):
        subaqueous_frame = tk.Frame(self.controller_panel)
        subaqueous_frame.grid(row=1, sticky=tk.EW)
        subaqueous_frame.columnconfigure(0, weight=1)

        tk.Label(subaqueous_frame,
                 text="Environmental Parameters",
                 font='Helvetica 10 bold').grid(
            row=0, pady=(10, 0), sticky=tk.EW)

        subaqueous_method_tabs = ttk.Notebook(subaqueous_frame)
        subaqueous_method_tabs.grid(row=1, column=0)
        tab1 = ttk.Frame(subaqueous_method_tabs)
        subaqueous_method_tabs.add(tab1, text='Water Surface')
        tab2 = ttk.Frame(subaqueous_method_tabs)
        subaqueous_method_tabs.add(tab2, text='Turbidity')
        water_surface_subframe = tk.Frame(tab1)
        water_surface_subframe.grid(row=1, column=0)

        self.water_surface_options = [
            "Riegl VQ-880-G",
            "Model (ECKV spectrum)"]

        self.windOptions = [w[0] for w in self.wind_vals.values()]

        self.waterSurfaceRadio = RadioFrame(
            water_surface_subframe, "Water Surface",
            self.water_surface_options, 1,
            callback=self.updateRadioEnable, width=self.control_panel_width)
        self.waterSurfaceRadio.grid(row=0, column=0, columnspan=1, sticky=tk.EW)

        self.windRadio = RadioFrame(water_surface_subframe, None, self.windOptions,
                                    1, width=self.control_panel_width-5)
        self.windRadio.grid(row=1, column=0, sticky=tk.E)

        turbidity_subframe = tk.Frame(tab2)
        turbidity_subframe.grid(row=2, column=0, sticky=(tk.N, tk.W, tk.E, tk.S))
        turbidity_subframe.columnconfigure(0, weight=1)
        turbidity_subframe.rowconfigure(0, weight=1)

        self.turbidity_options = ['{:s} ({:.2f}-{:.2f} m^-1)'.format(
            k[0], k[1][0] / 100.0, k[1][-1] / 100.0) for k in self.kd_vals.values()]

        self.turbidityRadio = RadioFrame(turbidity_subframe, "Turbidity (kd_490)",
                                         self.turbidity_options, 0,
                                         width=self.control_panel_width)
        self.turbidityRadio.grid(row=0, column=0, sticky=tk.N)

    def build_vdatum_input(self):
        datum_frame = tk.Frame(self.controller_panel)
        datum_frame.columnconfigure(0, weight=1)
        datum_frame.grid(row=3, sticky=tk.EW)
        tk.Label(datum_frame,
                 text="VDatum Region",
                 font='Helvetica 10 bold').grid(row=0, columnspan=1, pady=(10, 0), sticky=tk.EW)

        datum = Datum()
        regions, mcu_values, default_msg = datum.get_vdatum_region_mcus()
        self.vdatum_regions = dict({(key, value) for (key, value) in zip(regions, mcu_values)})
        self.vdatum_regions.update({default_msg: 0})
        self.vdatum_region = tk.StringVar(self)
        self.vdatum_region.set(default_msg)
        self.vdatum_region_option_menu = tk.OptionMenu(
            datum_frame,
            self.vdatum_region,
            *sorted(self.vdatum_regions.keys()),
            command=self.update_vdatum_mcu_value)
        self.vdatum_region_option_menu.config(width=self.control_panel_width, anchor='w')
        self.vdatum_region_option_menu.grid(sticky=tk.EW)

    def build_process_buttons(self):
        process_frame = tk.Frame(self.controller_panel)
        process_frame.grid(row=4, sticky=tk.NSEW)
        process_frame.columnconfigure(0, weight=0)

        label = tk.Label(process_frame, text='Process Buttons', font=NORM_FONT_BOLD)
        label.grid(row=0, columnspan=2, pady=(10, 0), sticky=tk.EW)

        self.sbet_btn_text = tk.StringVar(self)
        self.sbet_btn_text.set("Load Trajectory File(s)")
        self.sbetProcess = tk.Button(process_frame,
                                     textvariable=self.sbet_btn_text,
                                     width=self.control_panel_width,
                                     state=tk.DISABLED,
                                     command=self.sbet_process_callback)
        self.sbetProcess.grid(row=1, column=0, padx=(3, 0), sticky=tk.EW)

        self.tpu_btn_text = tk.StringVar(self)
        self.tpu_btn_text.set("Process TPU")
        self.tpuProcess = tk.Button(process_frame,
                                    textvar=self.tpu_btn_text,
                                    width=self.control_panel_width,
                                    state=tk.DISABLED,
                                    command=self.tpu_process_callback)
        self.tpuProcess.grid(row=2, column=0, padx=(3, 0), sticky=tk.EW)

    def update_vdatum_mcu_value(self, region):
        logging.info(self.vdatum_region.get())
        self.mcu = self.vdatum_regions[region]
        logging.info('The MCU for {} is {} cm.'.format(region, self.mcu))

    def update_button_enable(self):
        if self.sbetInput.directoryName != '':
            self.is_sbet_dir_set = True
            self.sbetProcess.config(state=tk.ACTIVE)
            self.controller.controller_configuration['directories'].update(
                {'sbet': self.sbetInput.directoryName})
            self.sbetInput.button.config(text="{} Directory Set".format('Trajectory'), fg='darkgreen')

        if self.lasInput.directoryName != '':
            self.is_las_dir_set = True
            self.controller.controller_configuration['directories'].update(
                {'las': self.lasInput.directoryName})
            self.lasInput.button.config(text="{} Directory Set".format('Las'), fg='darkgreen')

        if self.tpuOutput.directoryName != '':
            self.is_tpu_dir_set = True
            self.controller.controller_configuration['directories'].update(
                {'tpu': self.tpuOutput.directoryName})
            self.tpuOutput.button.config(text="{} Directory Set".format('TPU'), fg='darkgreen')

        if self.is_las_dir_set and self.is_tpu_dir_set and self.is_sbet_loaded:
            self.tpuProcess.config(state=tk.ACTIVE)

    def sbet_process_callback(self):
        self.sbet = Sbet(self.sbetInput.directoryName)
        self.sbet.set_data()
        self.is_sbet_loaded = True
        self.sbet_btn_text.set('Trajectory Loaded')  # TODO: do for compute, too
        self.sbetProcess.config(fg='darkgreen')
        self.update_button_enable()

    def tpu_process_callback(self):
        surface_ind = self.waterSurfaceRadio.selection.get()
        surface_selection = self.water_surface_options[surface_ind]

        wind_ind = self.windRadio.selection.get()
        wind_selection = self.windOptions[wind_ind]

        kd_ind = self.turbidityRadio.selection.get()
        kd_selection = self.turbidity_options[kd_ind]

        tpu = Tpu(surface_selection, surface_ind,
                  wind_selection, self.wind_vals[wind_ind][1], kd_selection,
                  self.kd_vals[kd_ind][1], self.vdatum_region.get(), self.mcu,
                  self.tpuOutput.directoryName)

        las_files = [os.path.join(self.lasInput.directoryName, l)
                     for l in os.listdir(self.lasInput.directoryName)
                     if l.endswith('.las')]

        def sbet_las_tiles_generator():
            """This generator is the 2nd argument for the
            run_tpu_multiprocessing method, to avoid
            passing entire sbet or list of tiled
            sbets to multiprocessing pool
            """

            tile_size = 500  # meters
            for las in las_files:  # 2016_422000e_2873500n.las
                las_base = las.split('\\')[-1]
                ul_x = float(las_base[5:11])
                ul_y = float(las_base[13:20])
                west = ul_x - tile_size
                east = ul_x + 2 * tile_size
                north = ul_y + tile_size
                south = ul_y - 2 * tile_size

                logging.info('({}) generating SBET tile...'.format(las.split('\\')[-1]))
                yield self.sbet.get_tile_data(north, south, east, west), las

        # tpu.run_tpu_multiprocessing(sbet_las_tiles_generator())
        tpu.run_tpu_singleprocess(sbet_las_tiles_generator())
        self.tpu_btn_text.set('TPU Calculated')
        self.tpuProcess.config(fg='darkgreen')

    def updateRadioEnable(self):
        """Updates the state of the windRadio, depending on waterSurfaceRadio."""
        if self.waterSurfaceRadio.selection.get() == 0:
            self.windRadio.setState(tk.DISABLED)
        else:
            self.windRadio.setState(tk.ACTIVE)


if __name__ == "__main__":
    app = CBlueApp()
    app.geometry('225x515')
    app.mainloop()  # tk functionality

