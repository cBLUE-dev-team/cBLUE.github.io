import os
import tkinter as tk
from tkinter import ttk
import json
import logging
import laspy
from .GuiSupport import DirectorySelectButton, RadioFrame
from .Datum import Datum
from .Sbet import Sbet
from .Tpu import Tpu
from .Merge import Merge
from .Subaerial import SensorModel, Jacobian

LARGE_FONT = ("Verdanna", 12)
NORM_FONT = ("Verdanna", 10)
NORM_FONT_BOLD = ("Verdanna", 10, "bold")
SMALL_FONT = ("Verdanna", 8)


class ControllerPanel(ttk.Frame):
    def __init__(self, parent, controller):
        ttk.Frame.__init__(self, parent)

        self.parent = parent
        self.controller = controller

        # I don't like this line of code!
        self.lastFileLoc = os.getcwd()

        ### Kd Labels and Indices ###
        self.kd_vals = [
            ("Clear", range(6, 11)),
            ("Clear-Moderate", range(11, 18)),
            ("Moderate", range(18, 26)),
            ("Moderate-High", range(26, 33)),
            ("High", range(33, 37)),
        ]

        ### Wind Labels and Indices ###
        self.wind_vals = [
            ("Calm-light air (0-2 kts)", [1]),
            ("Light Breeze (3-6 kts)", [2, 3]),
            ("Gentle Breeze (7-10 kts)", [4, 5]),
            ("Moderate Breeze (11-15 kts)", [6, 7]),
            ("Fresh Breeze (16-20 kts)", [8, 9, 10]),
        ]

        ### Names of sensors as displayed in GUI ###
        self.sensor_models = [
            "Riegl VQ-880-G (0.7 mrad)",
            "Riegl VQ-880-G (1.0 mrad)",
            "Riegl VQ-880-G (1.5 mrad)",
            "Riegl VQ-880-G (2.0 mrad)",
            "Leica Chiroptera 4X (HawkEye 4X Shallow)",
            "HawkEye 4X 400m AGL",
            "HawkEye 4X 500m AGL",
            "HawkEye 4X 600m AGL",
        ]

        self.is_sbet_dir_set = False
        self.is_las_dir_set = False
        self.is_tpu_dir_set = False
        self.is_sbet_loaded = False
        self.is_tpu_computed = False
        self.sbetInput = None
        self.lasInput = None
        self.tpuOutput = None
        self.sbet = None

        # Default region is no region
        self.mcu = 0

        #  Build the control panel
        self.control_panel_width = 30
        self.build_control_panel()

    def build_control_panel(self):
        self.controller_panel = ttk.Frame(self)
        self.controller_panel.grid(row=0, column=0, sticky=tk.EW)
        self.controller_panel.grid_rowconfigure(0, weight=1)
        self.build_directories_input()
        self.build_subaqueous_input()
        self.build_vdatum_input()
        self.build_sensor_input()
        self.build_error_type_input()
        self.build_output_csv()
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
            self,
            subaerial_frame,
            "Trajectory",
            self.controller.controller_config["directories"]["sbet"],
            self.control_panel_width,
            callback=self.update_button_enable,
        )
        self.sbetInput.grid(row=1, column=0)

        self.lasInput = DirectorySelectButton(
            self,
            subaerial_frame,
            "LAS",
            self.controller.controller_config["directories"]["las"],
            self.control_panel_width,
            callback=self.update_button_enable,
        )
        self.lasInput.grid(row=2, column=0)

        self.tpuOutput = DirectorySelectButton(
            self,
            subaerial_frame,
            "Output",
            self.controller.controller_config["directories"]["tpu"],
            self.control_panel_width,
            callback=self.update_button_enable,
        )
        self.tpuOutput.grid(row=3, column=0)

    def build_subaqueous_input(self):
        """
        This function builds the frame and tab toggle for
        selecting wind/kd ranges.
        Inputs: None
        Returns: Void
        """

        ### Frame layout (contains parameter widgets) ###
        subaqueous_frame = tk.Frame(self.controller_panel)
        subaqueous_frame.grid(row=1, sticky=tk.EW)
        subaqueous_frame.columnconfigure(0, weight=1)

        tk.Label(
            subaqueous_frame, text="Environmental Parameters", font="Helvetica 10 bold"
        ).grid(row=0, pady=(10, 0), sticky=tk.EW)

        ### Toggle between Wind and Kd panel tabs ###
        subaqueous_method_tabs = ttk.Notebook(subaqueous_frame)
        subaqueous_method_tabs.grid(row=1, column=0)

        ### Water Surface Frame ###
        tab1 = ttk.Frame(subaqueous_method_tabs)
        subaqueous_method_tabs.add(tab1, text="Water Surface")
        water_surface_subframe = tk.Frame(tab1)
        water_surface_subframe.grid(row=1, column=0)

        ### Turbidity Frame ###
        tab2 = ttk.Frame(subaqueous_method_tabs)
        subaqueous_method_tabs.add(tab2, text="Turbidity")
        turbidity_subframe = tk.Frame(tab2)
        turbidity_subframe.grid(row=2, column=0, sticky=(tk.N, tk.W, tk.E, tk.S))
        turbidity_subframe.columnconfigure(0, weight=1)
        turbidity_subframe.rowconfigure(0, weight=1)

        ### Set Wind ranges as radio buttons ###
        self.windRadio = RadioFrame(
            water_surface_subframe,  # where to put button
            "Wind Speed (kts)",  # give it a title
            [w[0] for w in self.wind_vals],  # list of options
            1,
            width=self.control_panel_width,  # width
        )
        self.windRadio.grid(row=1, column=0, sticky=tk.E)

        ### Set Kd ranges as radio buttons ###
        format_kd = lambda k: "{:s} ({:.2f}-{:.2f} m^-1)".format(
            k[0], k[1][0] / 100, k[1][-1] / 100
        )

        self.turbidityRadio = RadioFrame(
            turbidity_subframe,  # where to put button
            "Turbidity (kd_490)",  # give it a title
            [format_kd(k) for k in self.kd_vals],  # list of options
            0,
            width=self.control_panel_width,  # width
        )
        self.turbidityRadio.grid(row=0, column=0, sticky=tk.N)

    def build_vdatum_input(self):
        datum_frame = tk.Frame(self.controller_panel)
        datum_frame.columnconfigure(0, weight=1)
        datum_frame.grid(row=3, sticky=tk.EW)
        tk.Label(datum_frame, text="VDatum Region", font="Helvetica 10 bold").grid(
            row=0, columnspan=1, pady=(10, 0), sticky=tk.EW
        )

        datum = Datum()
        regions, mcu_values, default_msg = datum.get_vdatum_region_mcus()
        self.vdatum_regions = dict(
            {(key, value) for (key, value) in zip(regions, mcu_values)}
        )
        self.vdatum_regions.update({default_msg: 0})
        self.vdatum_region = tk.StringVar(self)
        self.vdatum_region.set(default_msg)
        self.vdatum_region_option_menu = tk.OptionMenu(
            datum_frame,
            self.vdatum_region,
            *sorted(self.vdatum_regions.keys()),
            command=self.update_vdatum_mcu_value,
        )
        self.vdatum_region_option_menu.config(
            width=self.control_panel_width, anchor="w"
        )
        self.vdatum_region_option_menu.grid(sticky=tk.EW)

    def build_sensor_input(self):
        ### Set up frame to hold dropdown menu ###
        sensor_frame = tk.Frame(self.controller_panel)
        sensor_frame.columnconfigure(0, weight=1)
        sensor_frame.grid(row=4, sticky=tk.EW)
        tk.Label(sensor_frame, text="Sensor Model", font="Helvetica 10 bold").grid(
            row=0, columnspan=1, pady=(10, 0), sticky=tk.EW
        )

        ### Holds the names of the selected sensor ###
        self.selected_sensor = tk.StringVar(self)

        ### Add sensor dropdown menu to GUI ###
        self.sensor_option_menu = tk.OptionMenu(
            sensor_frame,
            self.selected_sensor,
            *self.sensor_models,
            command=self.update_selected_sensor,
        )

        self.sensor_option_menu.config(width=self.control_panel_width, anchor="w")
        self.sensor_option_menu.grid(sticky=tk.EW)

    def update_selected_sensor(self, sensor):
        """
        Callback function for the sensor option menu.
        Updates the controller when a new sensor is selected.
        """

        self.selected_sensor = sensor
        self.controller.controller_config["sensor_model"] = sensor

    def build_error_type_input(self):

        ### 95% conf or 1 sigma ###
        self.error_types = ("1-\u03c3", "95% confidence")

        ### Set up frame to hold dropdown menu ###
        error_frame = tk.Frame(self.controller_panel)
        error_frame.columnconfigure(0, weight=1)
        error_frame.grid(row=5, sticky=tk.EW)
        tk.Label(error_frame, text="TPU Metric", font="Helvetica 10 bold").grid(
            row=0, columnspan=1, pady=(10, 0), sticky=tk.EW
        )

        ### Holds the names of the selected sensor ###
        self.error_type = tk.StringVar(self)

        ### Add sensor dropdown menu to GUI ###
        self.error_option_menu = tk.OptionMenu(
            error_frame,
            self.error_type,
            *self.error_types,
            command=None,  # self.update_error_type,
        )

        self.error_option_menu.config(width=self.control_panel_width, anchor="w")
        self.error_option_menu.grid(sticky=tk.EW)

    # def update_error_type(self, error_type):
    #     """
    #     Callback function for the sensor option menu.
    #     Updates the controller when a new sensor is selected.
    #     """
    #     self.selected_error = error_type
    #     self.controller.controller_config["error_type"] = error_type

    def build_output_csv(self):
        """
        Callback function to output points as csv_option
        """

        ### Set up frame to hold radio buttons ###
        csv_frame = tk.Frame(self.controller_panel)
        csv_frame.columnconfigure(0, weight=1)
        csv_frame.columnconfigure(1, weight=0)
        csv_frame.grid(row=6, sticky=tk.EW)
        tk.Label(csv_frame, text="Output Options", font="Helvetica 10 bold").grid(
            row=0, columnspan=2, pady=(10, 0), sticky=tk.EW
        )

        # Link buttons to bool variable to store csv option
        self.csv_option = tk.BooleanVar()
        self.extrabyte_button = ttk.Radiobutton(
            csv_frame, text="ExtraBytes", value=False, variable=self.csv_option
        )
        self.csv_button = ttk.Radiobutton(
            csv_frame, text="ExtraBytes + CSV", value=True, variable=self.csv_option
        )

        # Place buttons on grid
        self.extrabyte_button.grid(row=1, column=0, sticky=tk.W, padx=30)
        self.csv_button.grid(row=2, column=0, sticky=tk.W, padx=30)

    def build_process_buttons(self):
        process_frame = tk.Frame(self.controller_panel)
        process_frame.grid(row=7, sticky=tk.NSEW)
        process_frame.columnconfigure(0, weight=0)

        label = tk.Label(process_frame, text="Process Buttons", font=NORM_FONT_BOLD)
        label.grid(row=0, columnspan=2, pady=(10, 0), sticky=tk.EW)

        self.sbet_btn_text = tk.StringVar(self)
        self.sbet_btn_text.set("Load Trajectory File(s)")
        self.sbetProcess = tk.Button(
            process_frame,
            textvariable=self.sbet_btn_text,
            width=self.control_panel_width,
            state=tk.DISABLED,
            command=self.sbet_process_callback,
        )
        self.sbetProcess.grid(row=1, column=0, padx=(3, 0), sticky=tk.EW)

        self.tpu_btn_text = tk.StringVar(self)
        self.tpu_btn_text.set("Process TPU")
        self.tpuProcess = tk.Button(
            process_frame,
            textvar=self.tpu_btn_text,
            width=self.control_panel_width,
            state=tk.DISABLED,
            command=self.tpu_process_callback,
        )
        self.tpuProcess.grid(row=2, column=0, padx=(3, 0), sticky=tk.EW)

    def update_vdatum_mcu_value(self, region):
        self.mcu = self.vdatum_regions[region]

    def update_button_enable(self):
        if self.sbetInput.directoryName != "":
            self.is_sbet_dir_set = True
            self.sbetProcess.config(state=tk.ACTIVE)
            self.controller.controller_config["directories"].update(
                {"sbet": self.sbetInput.directoryName}
            )
            self.sbetInput.button.config(
                text="{} Directory Set".format("Trajectory"), fg="darkgreen"
            )

        if self.lasInput.directoryName != "":
            self.is_las_dir_set = True
            self.controller.controller_config["directories"].update(
                {"las": self.lasInput.directoryName}
            )
            self.lasInput.button.config(
                text="{} Directory Set".format("Las"), fg="darkgreen"
            )

        if self.tpuOutput.directoryName != "":
            self.is_tpu_dir_set = True
            self.controller.controller_config["directories"].update(
                {"tpu": self.tpuOutput.directoryName}
            )
            self.tpuOutput.button.config(
                text="{} Directory Set".format("TPU"), fg="darkgreen"
            )

        if self.is_las_dir_set and self.is_tpu_dir_set and self.is_sbet_loaded:
            self.tpuProcess.config(state=tk.ACTIVE)

    def sbet_process_callback(self):
        print(json.dumps(self.controller.controller_config, indent=1, sort_keys=True))
        self.sbet = Sbet(self.sbetInput.directoryName)
        self.sbet.set_data()
        self.is_sbet_loaded = True
        self.sbet_btn_text.set("Trajectory Loaded")
        self.sbetProcess.config(fg="darkgreen")
        self.update_button_enable()

    def tpu_process_callback(self):
        self.verify_water_level()

    def continue_with_tpu_calc(self, wseh_popup, wseh_value):
        self.controller.controller_config["water_surface_ellipsoid_height"] = wseh_value
        self.controller.save_config()
        wseh_popup.destroy()
        self.begin_tpu_calc()

    def verify_water_level(self):
        wseh = tk.Toplevel()
        tk.Toplevel.iconbitmap(wseh, "cBLUE_icon.ico")
        wseh.resizable(False, False)
        wseh.wm_title("IMPORTANT!!!")

        msg = "Enter the nominal water-surface ellipsoid height:\n(default value read from config file)"

        label = tk.Label(wseh, text=msg)
        label.pack()

        wseh_value = tk.StringVar(self)
        wseh_value.set(
            self.controller.controller_config["water_surface_ellipsoid_height"]
        )

        entry = tk.Entry(wseh, textvariable=wseh_value)
        entry.pack()

        b1 = ttk.Button(
            wseh,
            text="Ok",
            command=lambda: self.continue_with_tpu_calc(wseh, float(wseh_value.get())),
        )
        b1.pack()

        wseh.mainloop()

    def begin_tpu_calc(self):

        wind_ind = self.windRadio.selection.get()
        kd_ind = self.turbidityRadio.selection.get()

        # CREATE OBSERVATION EQUATIONS
        sensor_model = SensorModel(self.controller.controller_config["sensor_model"])

        multiprocess = self.controller.controller_config["multiprocess"]
        if multiprocess:
            num_cores = self.controller.controller_config["number_cores"]
            cpu_process_info = ("multiprocess", num_cores)
        else:
            cpu_process_info = ("singleprocess",)

        self.TPU_inputs = {
            "wind_val": self.wind_vals[wind_ind],
            "kd_val": self.kd_vals[kd_ind],
            "vdatum_region": self.vdatum_region.get(),
            "vdatum_region_mcu": self.mcu,
            "tpu_output": self.tpuOutput.directoryName,
            "cblue_version": self.controller.controller_config["cBLUE_version"],
            "sensor_model": self.controller.controller_config["sensor_model"],
            "cpu_process_info": cpu_process_info,
            "selected_sensor": self.selected_sensor,
            "subaqueous_luts": self.controller.controller_config["subaqueous_LUTs"],
            "water_surface_ellipsoid_height": self.controller.controller_config[
                "water_surface_ellipsoid_height"
            ],
            # "error_type": self.controller.controller_config["error_type"],
            "error_type": self.error_type.get(),
            "csv_option": self.csv_option.get(),
        }

        tpu = Tpu(**self.TPU_inputs)

        las_files = [
            os.path.join(self.lasInput.directoryName, l)
            for l in os.listdir(self.lasInput.directoryName)
            if l.endswith(".las") | l.endswith(".laz")
        ]

        num_las = len(las_files)

        # GENERATE JACOBIAN FOR SENSOR MODEL OBSVERVATION EQUATIONS
        jacobian = Jacobian(sensor_model)

        # CREATE OBJECT THAT PROVIDES FUNCTIONALITY TO MERGE LAS AND TRAJECTORY DATA
        merge = Merge()

        def sbet_las_tiles_generator():
            """This generator is the 2nd argument for the
            run_tpu_multiprocessing method, to avoid
            passing entire sbet or list of tiled
            sbets to the calc_tpu() method
            """

            for las_file in las_files:
                logging.cblue(
                    "({}) generating SBET tile...".format(os.path.split(las_file)[-1])
                )

                inFile = laspy.read(las_file)
                west = inFile.header.x_min
                east = inFile.header.x_max
                north = inFile.header.y_max
                south = inFile.header.y_min

                yield self.sbet.get_tile_data(
                    north, south, east, west
                ), las_file, jacobian, merge

        logging.cblue(
            "processing {} las file(s) ({})...".format(num_las, cpu_process_info[0])
        )

        logging.cblue(f"multiprocessing = {multiprocess} ({type(multiprocess)})")

        if multiprocess == "True":
            p = tpu.run_tpu_multiprocess(num_las, sbet_las_tiles_generator())

            self.tpu_btn_text.set("TPU Calculated")
            self.tpuProcess.config(fg="darkgreen")
            print("DONE!! (close cBLUE before running again)")

            p.close()
            p.join()
        elif multiprocess == "False":
            tpu.run_tpu_singleprocess(num_las, sbet_las_tiles_generator())
            self.tpu_btn_text.set("TPU Calculated")
            self.tpuProcess.config(fg="darkgreen")
            print("DONE!! (close cBLUE before running again)")

        else:
            logging.cblue(
                f"multiprocessing set to {multiprocess} (Must be True or False)"
            )

    def updateRadioEnable(self):
        """Updates the state of the windRadio, depending on waterSurfaceRadio."""
        if self.waterSurfaceRadio.selection.get() == 0:
            self.windRadio.setState(tk.DISABLED)
        else:
            self.windRadio.setState(tk.ACTIVE)
