from pathlib import Path
import pdal
import json
import rasterio
import rasterio.merge
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import os
import seaborn as sns
import numpy as np

sns.set(font_scale=1.5)
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (8, 8)

las_dir = Path('C:/QAQC_contract/marco_island/tpu_output')
las_files = list(las_dir.glob('*.las'))

for las in las_files:
    las_str = str(las).replace('\\', '/')
    print(las.name)

    gtiff_path = 'Z:/cBLUE/summary_test/{}.tif'.format(las.stem)

    pdal_json = """{
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
                "filename": """ + '"{}"'.format(gtiff_path) + """,
                "gdaldriver": "GTiff",
                "output_type": "mean",
                "resolution": "1.0",
                "type": "writers.gdal"
            }
        ]
    }"""

    pipeline = pdal.Pipeline(pdal_json)
    #pipeline.validate()

    count = pipeline.execute()
    #arrays = pipeline.arrays


tpu_dem_dir = Path('Z:/cBLUE/summary_test')
tpu_dems = list(tpu_dem_dir.glob('*.tif'))
tpu_dems_to_mosaic = []

for tpu_dem in tpu_dems:
    src = rasterio.open(tpu_dem)
    tpu_dems_to_mosaic.append(src)    
    
print(tpu_dems_to_mosaic)
mosaic, out_trans = rasterio.merge.merge(tpu_dems_to_mosaic)
mosaic[mosaic < 0] = np.nan
print(mosaic)

fig, ax = plt.subplots(1, 2, figsize=(10,10))
im = ax[0].imshow(mosaic.squeeze(), cmap='jet', vmin=20, vmax=50)
cax = fig.add_axes([0.1, 0.05, 0.35, 0.02])
fig.colorbar(im, cax=cax, orientation='horizontal')

ax[1].hist(mosaic.ravel(), bins=100, color='gray')
ax[1].set_xlim(0, 50)
ax[1].set(xlabel='Total TVU (cm)', ylabel='Count', title='Total TVU')

plt.show()
