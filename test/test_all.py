import json
import os
import shutil
from pathlib import Path

import pytest
from gpao_utils.store import Store

import altianalysis.bulk_differentiel as bulk_differentiel
import altianalysis.calcul_differentiel as calcul_differentiel
import altianalysis.gpao_differentiel as gpao_differentiel

# testing all routines

# calculDifferentiel -> per tile difference map calculation
# bulk_differentiel  -> per folder of tiles difference map calculation
# gpao_differentiel  --> à tester dans l'environnement de qualif

# from altianalysis import calculDifferentiel, bulk_differentiel, gpao_differentiel


TMP_PATH = Path("./tmp/main")

STORE = Store("local_store", "win_store", "unix_store")

URL_API = "http://localhost:8080/api/"


def setup_module(module):
    try:
        shutil.rmtree(TMP_PATH)
    except FileNotFoundError:
        pass
    os.makedirs(TMP_PATH)


@pytest.mark.docker
def test_calculDifferentiel():
    output_dir = TMP_PATH / "calculDifferentiel"
    output_dir.mkdir()
    dtm_lidar_file = "./data/lhd/Semis_2021_0886_6443_LA93_IGN69_50CM.tif"
    dtm_rge_alti = output_dir / "dtm_rge_alti.tif"
    out_difference_file = output_dir / "Difference_Semis_2021_0886_6443_LA93_IGN69_50CM.tif"
    calcul_differentiel._extract_rge_alti_tile_from_stream(dtm_lidar_file, dtm_rge_alti)
    calcul_differentiel._compute_difference_with_rge_alti(dtm_lidar_file, dtm_rge_alti, out_difference_file)


@pytest.mark.docker
def test_calculDifferentiel_nodata():
    output_dir = TMP_PATH / "calculDifferentiel_nodata"
    output_dir.mkdir()
    dtm_lidar_file = "./data/lhd/Semis_2021_0485_6196_LA93_IGN69_50CM.tif"
    dtm_rge_alti = output_dir / "dtm_rge_alti.tif"
    calcul_differentiel._extract_rge_alti_tile_from_stream(dtm_lidar_file, dtm_rge_alti)
    out_difference_file = output_dir / "Difference_Semis_2021_0485_6196_LA93_IGN69_50CM.tif"
    calcul_differentiel._compute_difference_with_rge_alti(dtm_lidar_file, dtm_rge_alti, out_difference_file)


@pytest.mark.docker
def test_bulk_differentiel():
    output_dir = TMP_PATH / "bulk_differentiel"
    output_dir.mkdir()
    dtm_lidar_dir = Path("./data/lhd_dir_gpao")
    bulk_differentiel.compute_all_difference_maps(dtm_lidar_dir, output_dir)


@pytest.mark.gpao
def test_gpao_differentiel_create_gpao_project():
    output_dir = TMP_PATH / "gpao_differentiel_create_gpao_project"
    output_dir.mkdir()
    dtm_lidar_lhds = Path("./data/lhd_dir_gpao")
    project_name = "test_create_gpao_project_difference_with_dem_rge_alti"
    project = gpao_differentiel.create_gpao_project(dtm_lidar_lhds, output_dir, STORE, project_name)

    assert project is not None

    project_json = json.loads(project.to_json())

    assert len(project_json["jobs"]) > 0

    assert project_json["name"].startswith(project_name)


"""
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
"""


"""
if __name__=="__main__":
    test_calculDifferentiel()
    test_bulk_differentiel()
    test_gpao_differentiel_create_gpao_project()
    test_gpao_run()

"""
