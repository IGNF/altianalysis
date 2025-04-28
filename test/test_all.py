import os, sys 
import os.path as osp
import pathlib
import numpy 
import rasterio
import typing
import numpy as np
import argparse
import logging
from rasterio.enums import Resampling
import requests
import tempfile
import time
from math import ceil


import json
import shutil
import subprocess as sp
import test.utils as tu
from pathlib import Path

import numpy as np
import pytest
from gpao_utils.gpao_test import wait_running_job
from gpao_utils.store import Store
# testing all routines 

# calculDifferentiel -> per tile difference map calculation 
# bulk_differentiel  -> per folder of tiles difference map calculation 
# gpao_differentiel  --> à tester dans l'environnement de qualif 

#from altianalysis import calculDifferentiel, bulk_differentiel, gpao_differentiel

import altianalysis.calculDifferentiel as calculDifferentiel
import altianalysis.bulk_differentiel as bulk_differentiel
import altianalysis.gpao_differentiel as gpao_differentiel

sys.path.append(osp.dirname(osp.dirname(osp.dirname(osp.dirname(__file__)))))

TMP_PATH = Path("./tmp/main")

STORE = Store("local_store", "win_store", "unix_store")

URL_API = "http://localhost:8080/api/"



def test_calculDifferentiel():
    dtm_lidar_file="./data/lhd/Semis_2021_0886_6443_LA93_IGN69_50CM.tif"
    tmp_dtm_rge_alti=calculDifferentiel._extract_rge_alti_tile_from_stream(dtm_lidar_file)
    out_difference_file="./data/lhd/Difference_Semis_2021_0886_6443_LA93_IGN69_50CM.tif"
    calculDifferentiel._compute_difference_with_rge_alti(dtm_lidar_file,tmp_dtm_rge_alti,out_difference_file)



def test_bulk_differentiel():
    dtm_lidar_dir=Path("./data/lhd_dir_gpao")
    out_difference_dir=Path("./delta/lhd_dir_gpao")
    bulk_differentiel.compute_all_difference_maps(dtm_lidar_dir,
                                                  out_difference_dir)
    

def test_gpao_differentiel_create_gpao_project():
    dtm_lidar_lhds=Path("./data/lhd_dir_gpao")
    out_difference_dtms=Path("./delta/lhd_dir_gpao_test")
    project_name="test_create_gpao_project_difference_with_dem_rge_alti"
    project= gpao_differentiel.create_gpao_project(dtm_lidar_lhds,out_difference_dtms,STORE,project_name)

    assert project is not None

    project_json= json.loads(project.to_json())

    assert len(project_json["jobs"]) > 0

    assert project_json["name"].startswith(project_name)



@pytest.mark.gpao
def test_gpao_run():
    dtm_lidar_lhds="./data/lhd_dir_gpao"
    out_difference_dtms="./delta/lhd_dir_gpao_test"
    project_name="test_run_gpao_difference_with_dem_rge_alti"

    gpao_hostname="localhost"

    runner_store_path = Path(dtm_lidar_lhds).resolve()
    local_store_path = Path("data/lhd_dir_gpao").resolve()

    gpao_differentiel.compute_on_gpao(
                        Path(dtm_lidar_lhds),
                        Path(out_difference_dtms),
                        gpao_hostname,
                        local_store_path,
                        runner_store_path,
                        project_name
                    )
    
    tu.execute_gpao_client(tags="docker", num_thread=4)
    wait_running_job(URL_API, project_name, delay_second=1, delay_log_second=10)




if __name__=="__main__":
    test_calculDifferentiel()
    test_bulk_differentiel()
    test_gpao_differentiel_create_gpao_project()
    test_gpao_run()




