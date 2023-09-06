from CBlueApp import CBlueApp
import argparse
import json
import os
from datetime import datetime


def get_help_text(options_list):
    help_text = "Choose an integer. "
    for n, option in enumerate(options_list):
        option = option.replace("%", "%%")  # Escape pct sign to avoid argparse error
        help_text += f"{n}={option}, "
    help_text = help_text.strip(", ")
    return help_text


# ADD ARGUMENTS

parser = argparse.ArgumentParser(description="Run CBlueApp without the GUI")
# Data Directories
parser.add_argument("in_sbet_dir", help="Trajectory Directory")
parser.add_argument("in_las_dir", help="LAS Directory")
parser.add_argument("output_dir", help="Output Directory")
# Environmental Parameters
# # Water Surface
wind_options = [
    "Calm-light air (0-2 kts)",
    "Light Breeze (3-6 kts)",
    "Gentle Breeze (7-10 kts)",
    "Moderate Breeze (11-15 kts)",
    "Fresh Breeze (16-20 kts)"
]
wind_values = [[1], [2, 3], [4, 5], [6, 7], [8, 9, 10]]
wind_help_text = get_help_text(wind_options)
parser.add_argument("wind", help=wind_help_text)
# # Turbidity
turbidity_options = [
    "Clear (0.06-0.10 m^-1)",
    "Clear-Moderate (0.11-0.17 m^-1)",
    "Moderate (0.18-0.25 m^-1)",
    "Moderate-High (0.26-0.32 m^-1)",
    "High (0.33-0.36 m^-1)"
]
turbidity_values = [[6, 11], [11, 18], [18, 26], [26, 33], [33, 37]]
turbidity_help_text = get_help_text(turbidity_options)
parser.add_argument("turbidity", help=turbidity_help_text)
# VDatum Region
parser.add_argument("mcu", default=0.0, help=r"Choose a number. See .\lookup_tables\V_Datum_MCU_Values.txt")
parser.add_argument("-vdatum_region", default=f"Used MCU value given in command",
                    help=r"Choose a string. This value is for logs only.")
# Sensor Model
with open("lidar_sensors.json", "r") as sensors_json:
    sensor_json_content = json.load(sensors_json)
sensor_options = list(sensor_json_content.keys())
sensor_help_text = get_help_text(sensor_options)
parser.add_argument("sensor", help=sensor_help_text)
# TPU Metric
tpu_metric_options = ["1-\u03c3", "95% confidence"]
tpu_help_text = get_help_text(tpu_metric_options)
parser.add_argument("tpu_metric", help=tpu_help_text)
# Output Options
parser.add_argument("--csv", action="store_true", help="Output CSV")
# Water Surface Ellipsoid Height
parser.add_argument("water_height", help="Choose a number. Nominal water surface ellipsoid height")

# PARSE ARGUMENTS
args = parser.parse_args()
in_sbet_dir = args.in_sbet_dir
in_las_dir = args.in_las_dir
output_dir = args.output_dir
wind_index = int(args.wind)
turbidity_index = int(args.turbidity)
mcu = args.mcu
vdatum_region = args.vdatum_region
sensor_index = int(args.sensor)
tpu_metric_index = int(args.tpu_metric)
csv = args.csv
water_height = args.water_height

# UPDATE CONFIG

with open("cblue_configuration.json", "r") as config:
    config_dict = json.load(config)
config_dict["command_line_interface"] = True
config_dict["directories"]["sbet"] = in_sbet_dir
config_dict["directories"]["las"] = in_las_dir
config_dict["directories"]["tpu"] = output_dir
config_dict["wind_ind"] = wind_index
config_dict["wind_selection"] = wind_options[wind_index]
config_dict["wind_vals"] = wind_values[wind_index]
config_dict["kd_ind"] = turbidity_index
config_dict["kd_selection"] = turbidity_options[turbidity_index]
config_dict["kd_vals"] = (turbidity_values[turbidity_index][0], turbidity_values[turbidity_index][1])
config_dict["vdatum_region"] = vdatum_region
config_dict["mcu"] = mcu
config_dict["sensor_model"] = sensor_options[sensor_index]
config_dict["error_type"] = tpu_metric_options[tpu_metric_index]
config_dict["csv_option"] = False
config_dict["water_surface_ellipsoid_height"] = water_height
time_object = datetime.now()
time_string = time_object.strftime("%Y-%m-%d_%H-%M-%S")
config_file = os.path.join(output_dir, f"config_{time_string}.json")
with open(config_file, "w") as custom_config:
    json.dump(config_dict, custom_config)

# RUN APP

CBlueApp(command_line_mode=True, config_file=config_file)

print("\n\nCOMMAND COMPLETE!\n\n")
