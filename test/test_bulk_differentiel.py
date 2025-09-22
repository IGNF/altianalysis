import os
import shutil
from pathlib import Path

import altianalysis.bulk_differentiel as bulk_differentiel

TMP_PATH = Path("./tmp/bulk_differentiel")


def setup_module(module):
    try:
        shutil.rmtree(TMP_PATH)
    except FileNotFoundError:
        pass
    os.makedirs(TMP_PATH)


def test_bulk_differentiel():
    output_dir = TMP_PATH / "bulk_differentiel"
    output_dir.mkdir()
    dtm_lidar_dir = Path("./data/lhd_dir_gpao")
    bulk_differentiel.compute_all_difference_maps(dtm_lidar_dir, output_dir)

    # check all difference maps are computed and stored in output_dir
    for lidar_dtm_file in dtm_lidar_dir.iterdir():
        if lidar_dtm_file.is_file() and str(lidar_dtm_file).endswith(".tif"):
            # check if corresponding difference file exists
            _matching_difference_file = output_dir / lidar_dtm_file.name
            assert os.path.exists(_matching_difference_file), "Difference file of {} is not computed!".format(
                lidar_dtm_file
            )
