import os
import shutil
from pathlib import Path

import numpy as np
import rasterio
from scipy.interpolate import RegularGridInterpolator

import altianalysis.compute_difference as compute_difference

TMP_PATH = Path("./tmp/compute_difference")


def setup_module(module):
    try:
        shutil.rmtree(TMP_PATH)
    except FileNotFoundError:
        pass
    os.makedirs(TMP_PATH)


def test_extract_rge_alti_tile_from_stream():
    output_dir = TMP_PATH / "extract_rge_alti_tile_from_stream"
    output_dir.mkdir()
    dtm_rge_alti = output_dir / "dtm_rge_alti.tif"
    dtm_lidar_file = "./data/lhd/Semis_2021_0886_6443_LA93_IGN69_50CM.tif"
    compute_difference._extract_rge_alti_tile_from_stream(dtm_lidar_file, dtm_rge_alti)

    # read dtm rge alti and dtm_lidar_file and check bounds
    with rasterio.open(dtm_lidar_file) as dtm_lidar, rasterio.open(dtm_rge_alti) as dtm_rge:

        bounds_dtm_lidar = dtm_lidar.bounds
        bounds_dtm_rge = dtm_rge.bounds

        assert (
            bounds_dtm_lidar == bounds_dtm_rge
        ), f"tiles extents are not matching: lidar dtm has ({bounds_dtm_lidar.left}, \
            {bounds_dtm_lidar.right}, {bounds_dtm_lidar.bottom}, {bounds_dtm_lidar.top}), \
                rge dtm has ({bounds_dtm_rge.left}, {bounds_dtm_rge.right}, {bounds_dtm_rge.bottom}, \
                    {bounds_dtm_rge.top})"


def test_compute_difference_between_dtms_with_self():
    output_dir = TMP_PATH / "compute_difference_between_dtms_with_self"
    output_dir.mkdir()
    dtm_lidar_file = "./data/lhd/Semis_2021_0886_6443_LA93_IGN69_50CM.tif"
    out_difference_file = output_dir / "Self_Difference_Semis_2021_0886_6443_LA93_IGN69_50CM.tif"
    compute_difference.compute_difference_between_dtms(dtm_lidar_file, dtm_lidar_file, out_difference_file)
    # read the self difference file  and check consistency
    with rasterio.open(out_difference_file) as out_diff_file:
        _diff = out_diff_file.read()
        assert np.all(_diff == 0), "difference with self yields non null values !"


# test simple difference with rge alti
def test_compute_difference_and_reconstruct():
    _epsilon = 0.5
    output_dir = TMP_PATH / "compute_difference_and_reconstruct"
    output_dir.mkdir()
    dtm_lidar_file = "./data/lhd/Semis_2021_0886_6443_LA93_IGN69_50CM.tif"
    dtm_rge_alti = output_dir / "dtm_rge_alti.tif"
    out_difference_file = output_dir / "Difference_Semis_2021_0886_6443_LA93_IGN69_50CM.tif"
    out_recomputed_lidar_file = output_dir / "Rebuilt_Semis_2021_0886_6443_LA93_IGN69_50CM.tif"
    compute_difference._extract_rge_alti_tile_from_stream(dtm_lidar_file, dtm_rge_alti)
    compute_difference.compute_difference_between_dtms(dtm_lidar_file, dtm_rge_alti, out_difference_file)

    # read files and check if we can reconstruct initial lidar image
    with rasterio.open(out_difference_file) as diff_file, rasterio.open(dtm_rge_alti) as dem_rge_file:
        diff = diff_file.read()
        dem_rge = dem_rge_file.read()

        meta_diff_lidar = diff_file.meta.copy()

        _, H, W = dem_rge.shape

        # upsample rge_alti dem using given ratio of GSDs
        ratio = diff_file.transform[0] / dem_rge_file.transform[0]

        # fit points
        fit_points = [np.arange(0, H), np.arange(0, W)]

        _interpolator = RegularGridInterpolator(
            fit_points, dem_rge[0, :, :], bounds_error=False, fill_value=dem_rge_file.nodata
        )

        points_ratio_x, points_ratio_y = np.meshgrid(
            np.arange(0, W - ratio, ratio), np.arange(0, H - ratio, ratio), indexing="ij"
        )

        test_points = np.array([points_ratio_x.ravel(), points_ratio_y.ravel()]).T

        _interpolated_dem_rge_at_ratio = _interpolator(test_points, method="cubic")

        _interpolated_dem_rge_at_ratio = np.reshape(
            _interpolated_dem_rge_at_ratio, (1, int((H - ratio) / ratio), int((W - ratio) / ratio))
        )

        _sum = diff[:, :-1, :-1] + _interpolated_dem_rge_at_ratio

        with rasterio.open(dtm_lidar_file) as dtm_lidar:
            lidar = dtm_lidar.read()[:, :-1, :-1]

            assert np.all(
                np.abs(_sum - lidar) < _epsilon
            ), "unable to reconstruct lidar data from difference file and reg alti dem !"

            # write reconstructed lidar dem
            with rasterio.open(out_recomputed_lidar_file, "w", **meta_diff_lidar) as dst:
                dst.write(_sum)


def test_compute_difference_with_nodata():
    output_dir = TMP_PATH / "compute_difference_with_nodata"
    output_dir.mkdir()
    # lidar dtm with nodata
    dtm_lidar_file = "./data/lhd/Semis_2021_0485_6196_LA93_IGN69_50CM.tif"
    dtm_rge_alti = output_dir / "dtm_rge_alti.tif"
    compute_difference._extract_rge_alti_tile_from_stream(dtm_lidar_file, dtm_rge_alti)
    out_difference_file = output_dir / "Difference_Semis_2021_0485_6196_LA93_IGN69_50CM.tif"
    compute_difference.compute_difference_between_dtms(dtm_lidar_file, dtm_rge_alti, out_difference_file)

    # check that there are no values when nodata
    with rasterio.open(out_difference_file) as computed_difference, rasterio.open(
        dtm_lidar_file
    ) as dtm_lidar, rasterio.open(dtm_rge_alti) as rge_alti:

        _diff = computed_difference.read()
        _dtm_lidar = dtm_lidar.read()
        rge_dem = rge_alti.read()

        # nodata
        nodata_diff_mask = _diff == computed_difference.nodata  # should capture the union of both nodata masks

        nodata_dtm_lidar = _dtm_lidar == dtm_lidar.nodata
        nodata_reg_alti = rge_dem == rge_alti.nodata

        # interpolate nodata_rge_alti in nearest neighbor mode (mask of nodata)

        _, H, W = rge_dem.shape

        _ratio = computed_difference.transform[0] / rge_alti.transform[0]

        # fit points
        fit_points = [np.arange(0, H), np.arange(0, W)]

        _interpolator = RegularGridInterpolator(fit_points, nodata_reg_alti[0, :, :], bounds_error=False, fill_value=0)

        _points_ratio_x, _points_ratio_y = np.meshgrid(
            np.arange(0, W - _ratio, _ratio), np.arange(0, H - _ratio, _ratio), indexing="ij"
        )

        test_points = np.array([_points_ratio_x.ravel(), _points_ratio_y.ravel()]).T

        _interpolated_dem_nodata = _interpolator(test_points, method="nearest")

        _interpolated_dem_nodata = np.reshape(
            _interpolated_dem_nodata, (1, int((H - _ratio) / _ratio), int((W - _ratio) / _ratio))
        )
        nodata_combined = np.logical_or(nodata_dtm_lidar[:, :-1, :-1], _interpolated_dem_nodata)

        assert np.all(nodata_diff_mask[:, :-1, :-1] == nodata_combined), "Added or missed nodata values !"


def test_main():
    output_dir = TMP_PATH / "main"
    output_dir.mkdir()
    dtm_lidar_file = "./data/lhd/Semis_2021_0886_6443_LA93_IGN69_50CM.tif"

    out_difference_file = output_dir / "Difference_with_rge_Semis_2021_0886_6443_LA93_IGN69_50CM.tif"

    compute_difference.main(dtm_lidar_file, out_difference_file)

    assert os.path.exists(out_difference_file), "difference with rge alti not computed !"
