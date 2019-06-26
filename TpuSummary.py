from pathlib import Path
import pdal
import json
import rasterio
import rasterio.merge
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from matplotlib.gridspec import GridSpec
import os
import seaborn as sns
import numpy as np
import pandas as pd


sns.set(font_scale=1.5)
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)

las_dir = Path('C:/QAQC_contract/marco_island/tpu_output')
las_files = list(las_dir.glob('*.las'))

for las in las_files:
    las_str = str(las).replace('\\', '/')
    print(las.name)

    gtiff_path_thu = 'Z:/cBLUE/summary_test/{}_THU.tif'.format(las.stem)
    gtiff_path_tvu = 'Z:/cBLUE/summary_test/{}_TVU.tif'.format(las.stem)

    pdal_jsons = """{
        "pipeline":[
            {
                "type": "readers.las",
                "extra_dims": "total_tvu=uint16",
                "filename": """ + '"{}"'.format(las_str) + """
            },
            {
                "type":"filters.range",
                "limits":"Z[-50:0],Classification[26:26]",
                "tag": "A"
            },
            {
                "inputs": ["A"],
                "dimension": "total_tvu",
                "filename": """ + '"{}"'.format(gtiff_path_tvu) + """,
                "gdaldriver": "GTiff",
                "output_type": "mean",
                "resolution": "1.0",
                "type": "writers.gdal"
            }
        ]
    }"""

    
    pipeline = pdal.Pipeline(p)
    #pipeline.validate()

    count = pipeline.execute()
    #arrays = pipeline.arrays


tpu_dem_dir = Path('Z:/cBLUE/summary_test')

tpu_thu_dems = list(tpu_dem_dir.glob('*_THU.tif'))
tpu_thu_dems_to_mosaic = []

tpu_tvu_dems = list(tpu_dem_dir.glob('*_TVU.tif'))
tpu_tvu_dems_to_mosaic = []

for tpu_thu_dem in tpu_thu_dems:
    src = rasterio.open(tpu_thu_dem)
    tpu_thu_dems_to_mosaic.append(src)    
    
for tpu_tvu_dem in tpu_tvu_dems:
    src = rasterio.open(tpu_tvu_dem)
    tpu_tvu_dems_to_mosaic.append(src)  


mosaic_thu, out_trans = rasterio.merge.merge(tpu_thu_dems_to_mosaic)
mosaic_thu[mosaic_thu < 0] = np.nan

mosaic_tvu, out_trans = rasterio.merge.merge(tpu_tvu_dems_to_mosaic)
mosaic_tvu[mosaic_tvu < 0] = np.nan


min_x = 0
max_x = 50

fig = plt.figure(constrained_layout=True)
fig.suptitle('cBLUE TPU Results Summary')

gs = GridSpec(3, 2, width_ratios=[1, 1], height_ratios=[1, 1, 1], hspace=0.5, wspace=0.35)
ax0 = fig.add_subplot(gs[:, 0])
ax1 = fig.add_subplot(gs[0, 1])
ax2 = fig.add_subplot(gs[1, 1])
ax3 = fig.add_subplot(gs[2, 1])

im = ax0.imshow(mosaic_tvu.squeeze(), cmap='jet', vmin=20, vmax=50)
cax = fig.add_axes([0.05, 0.3, 0.02, 0.3])
fig.colorbar(im, cax=cax, orientation='vertical')

tpu_stats = np.asarray([
    [np.nanmin(mosaic_thu), np.nanmax(mosaic_thu), np.nanmean(mosaic_thu), np.nanstd(mosaic_thu)],
    [np.nanmin(mosaic_tvu), np.nanmax(mosaic_tvu), np.nanmean(mosaic_tvu), np.nanstd(mosaic_tvu)]]).T
df_idx = ['min', 'max', 'mean', 'std']
df_cols = ['Total THU', 'Total TVU']
ax1.axis('tight')
ax1.axis('off')
ax1.table(cellText=tpu_stats.round(1), colLabels=df_cols, rowLabels=df_idx, bbox=[0, 0, 1, 1])

ax2.hist([-1], bins=100, color='gray')
ax2.set_xlim(min_x, max_x)
ax2.set_xticklabels([])
ax2.set(xlabel=None, ylabel='Count', title='Total THU')

ax3.hist(mosaic_tvu.ravel(), bins=100, color='gray')
ax3.set_xlim(min_x, max_x)
ax3.set(xlabel='(cm)', ylabel='Count', title='Total TVU')

plt.show()
