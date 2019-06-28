from pathlib import Path
import pdal
import rasterio
import rasterio.merge
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import numpy as np


def get_directories():
    #in_dir = Path(input('Enter tpu las directory:  '))
    #out_dir = Path(input('Enter results diretory:  '))

    in_dir = Path(r'Y:\2018\TBL_880_Eglin_Santa_Rosa_I_p\06_RIEGL_PROC\04_EXPORT\Green\04_TBL_880_Eglin_Santa_Rosa_I_g_gpsa_rf_wsf_rf_tm_flucs_elh')
    out_dir = Path(r'Z:\cBLUE\summary_test')

    return in_dir, out_dir


def get_tile_dems(dem_type):
    dems = []
    for dem in list(out_dir.glob('*_{}.tif'.format(dem_type.upper()))):
        src = rasterio.open(dem)
        dems.append(src)

    out_meta = src.meta.copy()  # uses last src made

    return dems, out_meta

        
def gen_mosaic(dems, out_meta):
    mosaic, out_trans = rasterio.merge.merge(dems)
    mosaic[mosaic < 0] = np.nan

    out_meta.update({
        "driver": "GTiff",
        "height": mosaic.shape[1],
        "width": mosaic.shape[2],
        "transform": out_trans})

    # save TPU mosaic DEMs
    mosaic_path = str(out_dir / '{}_DEM.tif'.format(dem_type.upper()))
    with rasterio.open(mosaic_path, 'w', **out_meta) as dest:
        dest.write(mosaic)
    
    return mosaic


def gen_pipline(dem_type, gtiff_path):
    #{
    #    "type":"filters.range",
    #    "limits":"Classification[2:26]"
    #},
    #{
    #    "type":"filters.range",
    #    "limits":"Classification!(2:26)",
    #    "tag": "A"
    #},
    pdal_json = """{
        "pipeline":[
            {
                "type": "readers.las",
                "filename": """ + '"{}"'.format(las_str) + """
            },
            {
                "type":"filters.returns",
                "groups":"last,only"
            },
            {
                "filename": """ + '"{}"'.format(gtiff_path) + """,
                "gdaldriver": "GTiff",
                "output_type": """ + '"{}"'.format(dem_type) + """,
                "resolution": "1.0",
                "type": "writers.gdal"
            }
        ]
    }"""
    print(pdal_json)

    return pdal_json


def create_dem(dem_type):
    gtiff_path = out_dir / '{}_{}.tif'.format(las.stem, dem_type.upper())
    gtiff_path = str(gtiff_path).replace('\\', '/')

    try:
        pipeline = pdal.Pipeline(gen_pipline(dem_type, gtiff_path))
        count = pipeline.execute()
    except Exception as e:
        print(e)
    pass


def gen_summary_graphic(mosaic, dem_type):
    fig = plt.figure(figsize=(7, 4))
    fig.suptitle('Standard Deviation DEM (DZ Surface Alternative)\n{}'.format('Eglin_Santa_Rosa_Island'))
    plt.subplots_adjust(left=0.15)

    gs = GridSpec(1, 2, width_ratios=[4, 1], height_ratios=[1], wspace=0.3)
    ax0 = fig.add_subplot(gs[0, 1])
    ax1 = fig.add_subplot(gs[0, 0])

    mosaic_stats = [np.nanmin(mosaic), np.nanmax(mosaic), 
                    np.nanmean(mosaic), np.nanstd(mosaic)]
    mosaic_stats = np.asarray([mosaic_stats]).T

    stats = ['min', 'max', 'mean', 'std']
    ax0.axis('tight')
    ax0.axis('off')
    ax0.table(cellText=mosaic_stats.round(3), colLabels=[dem_type], 
              rowLabels=stats, bbox=[0, 0, 1, 1])

    count, __, __ = ax1.hist(mosaic.ravel(), bins=np.arange(0, mosaic_stats[1], 0.01), 
                             color='gray')

    ax1.set(xlabel='meters', ylabel='Count')
    ax1.set_xlim(0, mosaic_stats[2] + 10 * mosaic_stats[3])

    #plt.tight_layout()
    plt.show()


if __name__ == '__main__':
    dem_type = 'mean'
    las_dir, out_dir = get_directories()

    # generate individual tile DEMs
    for las in list(las_dir.glob('*.las'))[0:]:
        las_str = str(las).replace('\\', '/')
        create_dem(dem_type)

    # mosaic tile DEMs
    dems, out_meta = get_tile_dems(dem_type)
    mosaic = gen_mosaic(dems, out_meta)
    gen_summary_graphic(mosaic, dem_type)
