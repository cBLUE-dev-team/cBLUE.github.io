from pathlib import Path
import pdal
import rasterio
import rasterio.merge
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import numpy as np


def get_directories():
    in_dir = Path(r'D:\04_FL1604-TB-N-880_g_gpsa_rf_ip_wsf_r_adj_qc\MarcoIsland\tpu_outdir')
    out_dir = Path(r'D:\04_FL1604-TB-N-880_g_gpsa_rf_ip_wsf_r_adj_qc\MarcoIsland\tpu_outdir\tDEMs')

    return in_dir, out_dir


def gen_pipeline(tpu, gtiff_path):
    '''"limits":"Z[-50:0],Classification[26:26]"'''
    pdal_json = """{
        "pipeline":[
            {
                "type": "readers.las",
                "extra_dims": "total_thu=uint16,total_tvu=uint16",
                "filename": """ + '"{}"'.format(las_str) + """
            },
            {
                "type":"filters.range",
                "limits":"Z[-50:0]",
                "tag": "A"
            },
            {
                "inputs": ["A"],
                "dimension": """ + '"total_{}"'.format(tpu) + """,
                "filename": """ + '"{}"'.format(gtiff_path) + """,
                "gdaldriver": "GTiff",
                "output_type": "mean",
                "resolution": "0.5",
                "type": "writers.gdal"
            }
        ]
    }"""

    return pdal_json


def create_tpu_dem(tpu):
    try:
        gtiff_path = out_dir / '{}_{}_ALLCLASSES.tif'.format(las.stem, tpu.upper())
        gtiff_path = str(gtiff_path).replace('\\', '/')
        pipeline = pdal.Pipeline(gen_pipeline(tpu, gtiff_path))
        count = pipeline.execute()
    except Exception as e:
        print(e)


def gen_summary_graphic(mosaics):
    min_x = 0
    max_x = 50

    fig = plt.figure(figsize=(6, 8))
    fig.suptitle('cBLUE TPU Results Summary\n{}'.format('Marco Island, FL'))
    fig.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.subplots_adjust(left=0.25)

    gs = GridSpec(3, 1, width_ratios=[1], height_ratios=[1, 1, 1], hspace=0.3)
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[1, 0])
    ax3 = fig.add_subplot(gs[2, 0])

    thu_stats = [np.nanmin(mosaics['thu']), 
                 np.nanmax(mosaics['thu']), 
                 np.nanmean(mosaics['thu']), 
                 np.nanstd(mosaics['thu'])]

    tvu_stats = [np.nanmin(mosaics['tvu']), 
                 np.nanmax(mosaics['tvu']), 
                 np.nanmean(mosaics['tvu']), 
                 np.nanstd(mosaics['tvu'])]

    tpu_stats = np.asarray([thu_stats, tvu_stats]).T

    df_idx = ['min', 'max', 'mean', 'std']
    df_cols = ['Total THU (cm)', 'Total TVU (cm)']
    ax1.axis('tight')
    ax1.axis('off')
    ax1.table(cellText=tpu_stats.round(1), colLabels=df_cols, rowLabels=df_idx, bbox=[0, 0, 1, 1])

    bins = range(0, 100)
    thu_count, __, __ = ax2.hist(mosaics['thu'].ravel(), bins=bins, color='gray', edgecolor='white')
    tvu_count, __, __ = ax3.hist(mosaics['tvu'].ravel(), bins=bins, color='gray', edgecolor='white')
    max_count = max(max(thu_count), max(tvu_count))
    
    ax2.set_xticklabels([])

    ax2.set_xticks(range(max_x), minor=True)
    ax3.set_xticks(range(max_x), minor=True)

    ax2.set(xlabel=None, ylabel='Count', title='Total THU')
    ax3.set(xlabel='(cm)', ylabel='Count', title='Total TVU')

    ax2.set_xlim(min_x, max_x)
    ax3.set_xlim(min_x, max_x)

    ax2.set_ylim(0, max_count + 0.1 * max_count)
    ax3.set_ylim(0, max_count + 0.1 * max_count)

    plt.tight_layout()
    plt.show()


if __name__ == '__main__':

    las_dir, out_dir = get_directories()

    tpu_dems = {'thu': [], 'tvu': []}
    tpu_dems_to_mosaic = {'thu': [], 'tvu': []}
    mosaics = {'thu': None, 'tvu': None}
    out_trans = {'thu': None, 'tvu': None}

    # generate individual tile DEMs
    for las in list(las_dir.glob('*.las')):
        las_str = str(las).replace('\\', '/')
        for tpu in ['thu', 'tvu']:
             create_tpu_dem(tpu)

    # mosaic TPU DEMs
    for tpu in ['thu', 'tvu']:
        for tpu_dem in list(out_dir.glob('*_{}_ALLCLASSES.tif'.format(tpu.upper()))):
            src = rasterio.open(tpu_dem)
            tpu_dems_to_mosaic[tpu].append(src)    

        mosaics[tpu], out_trans[tpu] = rasterio.merge.merge(tpu_dems_to_mosaic[tpu])
        mosaics[tpu][mosaics[tpu] < 0] = np.nan

        out_meta = src.meta.copy()  # uses last src made
        out_meta.update({
            "driver": "GTiff",
            "height": mosaics[tpu].shape[1],
            "width": mosaics[tpu].shape[2],
            "transform": out_trans[tpu]})

        # save TPU mosaic DEMs
        with rasterio.open(str(out_dir / '{}_DEM_ALLCLASSES.tif'.format(tpu.upper())), 'w', **out_meta) as dest:
            dest.write(mosaics[tpu])

    gen_summary_graphic(mosaics)
