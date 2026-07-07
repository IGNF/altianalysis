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
    parser = argparse.ArgumentParser(
        "compute difference between two elevation files or between one elevation file and rge alti"
    )
    parser.add_argument("--primary_elevation_file", type=str, help="primary elevation file")
    parser.add_argument(
        "--second_elevation_file",
        default=None,
        type=str,
        help="secondary elevation file to compare with primary elevation file. "
        "If not provided, primary elevation file is compared with rge alti (1 meter) data stream",
    )
    parser.add_argument("--name_save_out", type=str, help="name of difference file")
    parser.add_argument("--stream_type", action="store_true", help="type of stream to use (RGEALTI or LIDARHD)")
    return parser.parse_args()


def _extract_tiles_from_stream(
    dtm_file: str,
    output_path: str | Path,
    stream="RGEALTI-MNT_PYR-ZIP_FXX_LAMB93_WMS",  # "ELEVATION.ELEVATIONGRIDCOVERAGE.HIGHRES",
    proj="2154",
    pixel_per_meter=1,
    timeout_second=300,
    check_images=False,
):

    # compute dtm lidar extent while reading with rasterio
    with rasterio.open(dtm_file) as dtm:
        bounds = dtm.bounds
        minx, miny, maxx, maxy = bounds.left, bounds.bottom, bounds.right, bounds.top

    try:
        download_image(
            proj,
            layer=stream,
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
        warnings.warn(f"Request time out for stream associated to {dtm_file}")
        return False


def compute_difference_between_dtms(first_dtm_file: str, second_dtm_file: str, name_save_out: str) -> None:

    # read dtm_lidar tile
    with rasterio.open(first_dtm_file) as dtm_1, rasterio.open(second_dtm_file) as dtm_2:

        # read dtm_lidar array
        data_dtm_1 = dtm_1.read(1)

        # copy metadata of mtd_lidar
        meta_dtm_1 = dtm_1.meta.copy()

        # window from rge alti
        window_2 = dtm_2.window(*dtm_1.bounds)

        # read the data from dtm_rge with the same window as dtm_lidar
        data_dtm_2_windowed = dtm_2.read(
            1,
            window=window_2,
            boundless=True,
            out_shape=data_dtm_1.shape,
            resampling=Resampling.cubic,
            fill_value=0,
        )

        # data_dtm_rge_windowed=np.where(data_dtm_rge_windowed==dtm_rge.nodata, 0,data_dtm_rge_windowed)

        # difference dem
        _difference = data_dtm_1 - data_dtm_2_windowed

        _masq_nodata = np.logical_or((data_dtm_2_windowed == dtm_2.nodata), (data_dtm_1 == dtm_1.nodata))

        _difference[_masq_nodata] = dtm_1.nodata

        # save result
        with rasterio.open(name_save_out, "w", **meta_dtm_1) as dst:
            dst.write(_difference, 1)


def main(reference_dtm_file: Path | str, secondary_dtm_file: Path | str | None, output_difference_file: Path | str, stream_type: str = None):

    if secondary_dtm_file:
        compute_difference_between_dtms(reference_dtm_file, secondary_dtm_file, output_difference_file)

    else:
        with open("data/stream_types.txt", "r") as f:
            for l in f:
                if stream_type in l:
                    stream_value = l.split(" ")[1]

        with tempfile.NamedTemporaryFile(suffix="_dtm_temp.tif", delete=False) as tmp:
            success = _extract_tiles_from_stream(
                reference_dtm_file, pixel_per_meter=5, output_path=tmp.name, stream=stream_value
            )

            if success:
                compute_difference_between_dtms(reference_dtm_file, tmp, output_difference_file)

    # elif use_lidarHD:

    #     with tempfile.NamedTemporaryFile(suffix="_dtm_lidarHD.tif", delete=False) as tmp_lidarHD:
    #         success = _extract_tiles_from_stream(
    #             reference_dtm_file, pixel_per_meter=5, output_path=tmp_lidarHD.name, stream="IGNF_LIDAR-HD_MNT_ELEVATION.ELEVATIONGRIDCOVERAGE.LAMB93"
    #         )

    #         if success:
    #             compute_difference_between_dtms(reference_dtm_file, tmp_lidarHD, output_difference_file)

    # else:

    #     with tempfile.NamedTemporaryFile(suffix="_dtm_rgealti.tif", delete=False) as tmp_rge:

    #         success = _extract_tiles_from_stream(
    #             reference_dtm_file, pixel_per_meter=5, output_path=tmp_rge.name
    #         )

    #         if success:
    #             compute_difference_between_dtms(reference_dtm_file, tmp_rge, output_difference_file)


if __name__ == "__main__":
    args = parse_args()
    main(args.primary_elevation_file, args.second_elevation_file, args.name_save_out, args.use_lidarHD)
