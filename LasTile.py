from pathlib import Path
from shapely.geometry import Polygon
from shapely.ops import transform
import pyproj
from pyproj import CRS
from functools import partial
import subprocess
import json
from osgeo import osr
import geopandas as gpd
from tqdm import tqdm
import re


def run_console_cmd(cmd):
    process = subprocess.Popen(
        cmd.split(' '), shell=False, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.DEVNULL)
    output, error = process.communicate()
    returncode = process.poll()
    return returncode, output


def get_tiles_template():
    bboxes = []
    attributes = {
        'name': [],
        'parent': [],
        'hor_srs': [],
        'las_version': [],
        }
    return bboxes, attributes


wgs84_epsg = 'epsg:4326'
gpkg = Path(r'D:/04_FL1604-TB-N-880_g_gpsa_rf_ip_wsf_r_adj_qc/MarcoIsland/las_files.gpkg')
geojson_path = Path(r'D:/04_FL1604-TB-N-880_g_gpsa_rf_ip_wsf_r_adj_qc/MarcoIsland/las_tiles.geojson')

las_dir = Path(r'D:/04_FL1604-TB-N-880_g_gpsa_rf_ip_wsf_r_adj_qc/MarcoIsland/las_files')
lasses = list(las_dir.rglob('*.las'))

bboxes, attributes = get_tiles_template()

las_count = 0
block_count = 0
block_size = 500

for las_path in tqdm(lasses):

    las = str(las_path).replace('\\', '/')
    cmd_str = 'pdal info {} --metadata'.format(las)
    las_count += 1

    #reg_str = r'04_.*_qc'
    #if re.search(reg_str, las_path.parent.name):

    try:
        metadata = run_console_cmd(cmd_str)[1].decode('utf-8')
        meta_dict = json.loads(metadata)['metadata']

        major_version = meta_dict['major_version']
        minor_version = meta_dict['minor_version']
        las_version = f'{major_version}.{minor_version}'

        hor_wkt = meta_dict['srs']['horizontal']
        hor_srs = osr.SpatialReference(wkt=hor_wkt) 
        projcs = hor_srs.GetAttrValue('projcs')

        minx = meta_dict['minx']
        miny = meta_dict['miny']
        maxx = meta_dict['maxx']
        maxy = meta_dict['maxy']

        tile_coords = [
                (minx, miny),
                (minx, maxy),
                (maxx, maxy),
                (maxx, miny)
            ]

        project = partial(
            pyproj.transform,
            pyproj.Proj(CRS.from_string(projcs)),
            pyproj.Proj(wgs84_epsg))

        bboxes.append(transform(project, Polygon(tile_coords)))

        attributes['name'].append(las_path.name)
        attributes['parent'].append(str(las_path.parent))
        attributes['hor_srs'].append(projcs)
        attributes['las_version'].append(las_version)

        if las_count % block_size == 0 or las_count < block_size:
            block_count += 1
            print('creating GeoDataFrame...')
            gdf = gpd.GeoDataFrame(geometry=bboxes, crs=wgs84_epsg)
            gdf.geometry = gdf.geometry.map(lambda poly: transform(lambda x, y: (y, x), poly))

            gdf['name'] = attributes['name']
            gdf['parent'] = attributes['parent']
            gdf['hor_srs'] = attributes['hor_srs']
            gdf['las_version'] = attributes['las_version']

            print(f'writing to {gpkg}...')
            layer = f'MarcoIsland_{block_count}'
            #bboxes, attributes = get_tiles_template()
            #gdf.to_file(gpkg, layer=layer, driver='GPKG')
            
        gdf.to_file(geojson_path, driver='GeoJSON')

    except Exception as e:
        print(f'{e} - {str(las_path)}')
