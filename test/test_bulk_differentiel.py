import os
import shutil
from pathlib import Path

import altianalysis.bulk_differentiel as bulk_differentiel

TMP_PATH = Path("./tmp/main")


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
