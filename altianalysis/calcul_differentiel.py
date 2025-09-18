import argparse
import tempfile
import warnings
from pathlib import Path

import numpy as np
import rasterio
import requests
from pdaltools.download_image import download_image
from rasterio.enums import Resampling


def parse_args():
    parser = argparse.ArgumentParser("compute difference map between lidar dtm and rge alti")
    parser.add_argument("--dtm_lidar_file", type=str, help="dtm lidar tif file")
    # parser.add_argument("--dtm_rge_tile", type=str, help="rge alti tif file")
    parser.add_argument("--name_save_out", type=str, help="name of difference file")
    return parser.parse_args()


def _extract_rge_alti_tile_from_stream(
    dtm_lidar_file: str,
    output_path: str | Path,
    stream_RGE="RGEALTI-MNT_PYR-ZIP_FXX_LAMB93_WMS",  # "ELEVATION.ELEVATIONGRIDCOVERAGE.HIGHRES",
    proj="2154",
    pixel_per_meter=1,
    timeout_second=300,
    check_images=False,
):

    # compute dtm lidar extent while reading with rasterio
    with rasterio.open(dtm_lidar_file) as dtm_lhd:
        bounds = dtm_lhd.bounds
        minx, miny, maxx, maxy = bounds.left, bounds.bottom, bounds.right, bounds.top

    try:
        download_image(
            proj,
            layer=stream_RGE,
            minx=minx,
            miny=miny,
            maxx=maxx,
            maxy=maxy,
            pixel_per_meter=pixel_per_meter,
            outfile=output_path,
            timeout=timeout_second,
            check_images=check_images,
            size_max_gpf=5000,
        )
        return True

    except requests.exceptions.Timeout:
        warnings.warn(f"Request time out for stream associated to {dtm_lidar_file}")
        return False


def compute_difference_between_dtms(dtm_lidar_file: str, dtm_rge_tile: str, name_save_out: str) -> None:

    # read dtm_lidar tile
    with rasterio.open(dtm_lidar_file) as dtm_lidar, rasterio.open(dtm_rge_tile) as dtm_rge:

        # read dtm_lidar array
        data_dtm_lidar = dtm_lidar.read(1)

        # copy metadata of mtd_lidar
        meta_dtm_lidar = dtm_lidar.meta.copy()

        # window from rge alti
        window_rge = dtm_rge.window(*dtm_lidar.bounds)

        # read the data from dtm_rge with the same window as dtm_lidar
        data_dtm_rge_windowed = dtm_rge.read(
            1,
            window=window_rge,
            boundless=True,
            out_shape=data_dtm_lidar.shape,
            resampling=Resampling.cubic,
            fill_value=0,
        )

        # data_dtm_rge_windowed=np.where(data_dtm_rge_windowed==dtm_rge.nodata, 0,data_dtm_rge_windowed)

        # difference dem
        _difference = data_dtm_lidar - data_dtm_rge_windowed

        _masq_nodata = np.logical_or((data_dtm_rge_windowed == dtm_rge.nodata), (data_dtm_lidar == dtm_lidar.nodata))

        _difference[_masq_nodata] = dtm_lidar.nodata

        # save result
        with rasterio.open(name_save_out, "w", **meta_dtm_lidar) as dst:
            dst.write(_difference, 1)


def main():
    args = parse_args()

    with tempfile.NamedTemporaryFile(suffix="_dtm_rgealti.tif", delete=False) as tmp_rge:

        success = _extract_rge_alti_tile_from_stream(args.dtm_lidar_file, pixel_per_meter=5, output_path=tmp_rge.name)

        if success:
            compute_difference_between_dtms(args.dtm_lidar_file, tmp_rge, args.name_save_out)


if __name__ == "__main__":
    main()
