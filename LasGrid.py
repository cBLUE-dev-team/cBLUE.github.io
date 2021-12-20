import os
from pathlib import Path
import pdal
import rasterio
import rasterio.merge
from tqdm import tqdm
import pathos.pools as pp


class QuickLook:
    def __init__(self, out_dir):
        self.out_meta = None
        self.out_dir = out_dir

    def get_tile_dems(self, mtype):
        print(f"retreiving individual {mtype} grids...")
        dems = []
        for dem in list(self.out_dir.glob(f"*_{mtype}.tif")):
            print(dem)
            src = rasterio.open(dem)
            dems.append(src)
        self.out_meta = src.meta.copy()  # uses last src made
        return dems

    def gen_mosaic(self, mtype):

        quick_look_path = self.out_dir / f"QUICK_LOOK_{mtype}.tif"

        dems = self.get_tile_dems(mtype)
        if dems:
            print("generating {}...".format(quick_look_path))
            mosaic, out_trans = rasterio.merge.merge(dems)
            self.out_meta.update(
                {
                    "driver": "GTiff",
                    "height": mosaic.shape[1],
                    "width": mosaic.shape[2],
                    "transform": out_trans,
                }
            )

            with rasterio.open(quick_look_path, "w", **self.out_meta) as dest:
                dest.write(mosaic)
        else:
            print("No DEM tiles were generated.")

    def gen_mean_z_surface(self, las_path):
        import pdal
        from pathlib import Path

        las_str = str(las_path).replace("\\", "/")

        extra_bytes = ["total_tvu"]

        for eb in extra_bytes:

            gtiff_path = self.out_dir / las_path.name.replace(".las", f"_{eb}.tif")
            gtiff_path = str(gtiff_path).replace("\\", "/")

            pdal_json = (
                """{
                "pipeline":[
                    {
                        "type": "readers.las",
                        "filename": """
                + '"{}"'.format(las_str)
                + """,
                        "extra_dims": """
                + '"{}=float"'.format(eb)
                + """,
                        "use_eb_vlr": "true"
                    },
                    {
                        "type":"filters.range",
                        "limits": "Classification[26:26]"
                    },
                    {
                        "filename": """
                + '"{}"'.format(gtiff_path)
                + """,
                        "dimension": """
                + '"{}"'.format(eb)
                + """,
                        "gdaldriver": "GTiff",
                        "output_type": "mean",
                        "resolution": "0.5",
                        "type": "writers.gdal"
                    }
                ]
            }"""
            )

            try:
                pipeline = pdal.Pipeline(pdal_json)
                __ = pipeline.execute()
                arrays = pipeline.arrays
                print(arrays)
                metadata = pipeline.metadata
            except Exception as e:
                print(e)

    def gen_mean_z_surface_multiprocess(self, las_paths):
        p = pp.ProcessPool(4)
        num_las_paths = len(list(las_paths))
        for _ in tqdm(
            p.imap(self.gen_mean_z_surface, las_paths), total=num_las_paths, ascii=True
        ):
            pass
        p.close()
        p.join()


def set_env_vars(env_name):
    user_dir = os.path.expanduser("~")
    conda_dir = Path(user_dir).joinpath("AppData", "Local", "Continuum", "anaconda3")
    env_dir = conda_dir / "envs" / env_name
    share_dir = env_dir / "Library" / "share"
    script_path = conda_dir / "Scripts"
    gdal_data_path = share_dir / "gdal"
    proj_lib_path = share_dir

    if script_path.name not in os.environ["PATH"]:
        os.environ["PATH"] += os.pathsep + str(script_path)
    os.environ["GDAL_DATA"] = str(gdal_data_path)
    os.environ["PROJ_LIB"] = str(proj_lib_path)


def main():

    set_env_vars("cblue_diag")

    las_dir = Path(r"D:\JeromesCreek\tpu_dir")
    las_paths = list(las_dir.glob("*.las"))

    out_dir = las_dir / "DEMs"

    ql = QuickLook(out_dir)
    ql.gen_mean_z_surface_multiprocess(las_paths)

    ql.gen_mosaic("total_tvu")


if __name__ == "__main__":
    main()
# dummy comment
