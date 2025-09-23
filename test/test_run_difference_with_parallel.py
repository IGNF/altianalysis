import os
import shutil
from pathlib import Path

import altianalysis.run_difference_with_parallel as run_difference_with_parallel

TMP_PATH = Path("./tmp/run_diffrerence_with_parallel")


def setup_module(module):
    try:
        shutil.rmtree(TMP_PATH)
    except FileNotFoundError:
        pass
    os.makedirs(TMP_PATH)


def test_compute_all_difference_maps():
    output_dir = TMP_PATH / "compute_all_difference_maps"
    output_dir.mkdir()
    dtm_lidar_dir = Path("./data/lhd_dir_gpao")
    run_difference_with_parallel.compute_all_difference_maps(dtm_lidar_dir, output_dir)

    # check all difference maps are computed and stored in output_dir
    for lidar_dtm_file in dtm_lidar_dir.iterdir():
        if lidar_dtm_file.is_file() and str(lidar_dtm_file).endswith(".tif"):
            # check if corresponding difference file exists
            _matching_difference_file = output_dir / lidar_dtm_file.name
            assert os.path.exists(_matching_difference_file), "Difference file of {} is not computed!".format(
                lidar_dtm_file
            )
