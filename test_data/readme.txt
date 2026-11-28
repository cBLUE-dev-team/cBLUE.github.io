
This folder contains a LAS file snippet (CM_subset.las) and corresponding trajectory snippet (20260425_SN0003_lift02_trimmed.txt) for testing purposes. These files should be copied to separate folders on your computer, since you will need to specify a LAS file folder and trajectory folder. Recommended parameter settings are: 
Sensor model: CoastalMapper
Water Surface: Gentle Breeze (8-12] kts
Turbidity: Moderate-Turbid (0.21-0.27] m^-1
TPU Metric: 95% confidence
Bin length: 10.0
Don't include VDatum uncertainty
Processing in cBLUE v5.0 with these settings should yield the following .json file ouput:
{
 "Wind speed": "Gentle Breeze (8-12] kts",
 "Turbidity": "Moderate-Turbid (0.21-0.27] m^-1",
 "VDatum region": "Don't Include Datum Transformation Uncertainty",
 "VDatum region MCU": "0.0",
 "Optional VUC": 0.0,
 "Optional HUC": 0.0,
 "Flight line stats (min max mean stddev)": {
  "106 (474040/474040 points with TPU)": [
   "total_thu: 0.134 0.990 0.342 0.259",
   "total_tvu: 0.051 0.140 0.084 0.040"
  ],
  "20105 (627/628 points with TPU)": [
   "total_thu: 0.148 0.177 0.165 0.004",
   "total_tvu: 0.069 0.078 0.075 0.001"
  ],
  "20106 (25309/25309 points with TPU)": [
   "total_thu: 0.088 0.179 0.136 0.011",
   "total_tvu: 0.045 0.078 0.061 0.004"
  ],
  "20107 (64/65 points with TPU)": [
   "total_thu: 0.156 0.168 0.163 0.003",
   "total_tvu: 0.073 0.077 0.076 0.001"
  ]
 },
 "Sensor model": "CoastalMapper",
 "cBLUE version": "v5.0",
 "Subaqueous processing version": "v4.0",
 "CPU processing": [
  "singleprocess"
 ],
 "Water surface tile length": 10.0,
 "Error type": "95% confidence"
