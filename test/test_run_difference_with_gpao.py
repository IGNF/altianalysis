import os
import shutil
import test.utils as tu
from pathlib import Path

import pytest
from gpao_utils.gpao_test import wait_running_job
from gpao_utils.store import Store

import altianalysis.run_difference_with_gpao as run_difference_with_gpao

TMP_PATH = Path("./tmp/run_difference_with_gpao")

STORE = Store("local_store", "win_store", "unix_store")


def setup_module(module):
    try:
        shutil.rmtree(TMP_PATH)
    except FileNotFoundError:
        pass
    os.makedirs(TMP_PATH)


def test_create_main_gpao_project():
    # No need to create the output dir, this test does not run the gpao projects
    output_dir = TMP_PATH / "create_main_gpao_project"
    dtm_lidar_lhds = Path("./data/lhd_dir_gpao")
    project_name = "test_create_gpao_project_difference_with_dem_rge_alti"
    project = run_difference_with_gpao.create_main_gpao_project(dtm_lidar_lhds, None, output_dir, STORE, project_name)

    assert project is not None

    assert len(project.jobs) == 5

    assert project.name.startswith(project_name)


def test_create_gpao_projects_with_cog():
    # No need to create the output dir, this test does not run the gpao projects
    output_dir = TMP_PATH / "create_gpao_projects_with_cog"
    dtm_lidar_lhds = Path("./data/lhd_dir_gpao")
    cog_filename = "cog.tif"
    project_name = "test_create_gpao_project_difference_with_dem_rge_alti"
    projects = run_difference_with_gpao.create_gpao_projects(
        dtm_lidar_lhds, None, output_dir, STORE, project_name, cog_filename
    )

    assert len(projects) == 2
    assert len(projects[0].jobs) == 5
    assert len(projects[1].jobs) == 1


def test_create_gpao_projects_without_cog():
    # No need to create the output dir, this test does not run the gpao projects
    output_dir = TMP_PATH / "create_gpao_projects_without_cog"
    dtm_lidar_lhds = Path("./data/lhd_dir_gpao")
    project_name = "test_create_gpao_project_difference_with_dem_rge_alti"
    projects = run_difference_with_gpao.create_gpao_projects(dtm_lidar_lhds, None, output_dir, STORE, project_name, "")

    assert len(projects) == 1
    assert len(projects[0].jobs) == 5


@pytest.mark.gpao
def test_gpao_run_with_cog_stream_rge():
    dtm_lidar_lhds = "./data/lhd_dir_gpao"
    output_dir = TMP_PATH / "gpao_run_with_cog_stream_rge"
    output_dir.mkdir()
    cog_filename = "cog.tif"
    project_name = "test_run_altianalysis_gpao"

    gpao_hostname = os.environ.get("GPAO_API_URL", "localhost")
    url_api = f"http://{gpao_hostname}:8080/api/"

    runner_store_path = Path(dtm_lidar_lhds).resolve()
    local_store_path = Path("data/lhd_dir_gpao").resolve()

    run_difference_with_gpao.compute_on_gpao(
        Path(dtm_lidar_lhds),
        None,
        Path(output_dir),
        gpao_hostname,
        local_store_path,
        runner_store_path,
        project_name,
        cog_filename=cog_filename,
    )

    if gpao_hostname == "localhost":
        tu.execute_gpao_client(tags="docker", num_thread=4)
    wait_running_job(url_api, project_name, delay_second=1, delay_log_second=10)

    assert (
        len([f for f in os.listdir(output_dir) if os.path.splitext(f)[-1] == ".tif"]) == 6
    )  # 5 individual output files + cog

    assert (output_dir / cog_filename).is_file()


@pytest.mark.gpao
def test_gpao_run_without_cog_stream_rge():
    dtm_lidar_lhds = "./data/lhd_dir_gpao"
    output_dir = TMP_PATH / "gpao_run_without_cog_stream_rge"
    output_dir.mkdir()
    project_name = "test_run_altianalysis_gpao_stream"

    gpao_hostname = os.environ.get("GPAO_API_URL", "localhost")
    url_api = f"http://{gpao_hostname}:8080/api/"

    runner_store_path = Path(dtm_lidar_lhds).resolve()
    local_store_path = Path("data/lhd_dir_gpao").resolve()

    run_difference_with_gpao.compute_on_gpao(
        Path(dtm_lidar_lhds), None, Path(output_dir), gpao_hostname, local_store_path, runner_store_path, project_name
    )

    if gpao_hostname == "localhost":
        tu.execute_gpao_client(tags="docker", num_thread=4)
    wait_running_job(url_api, project_name, delay_second=1, delay_log_second=10)


@pytest.mark.gpao
def test_gpao_run_without_cog_given_secondary_folder():
    dtm_lidar_lhds = "./data/lhd_dir_gpao"
    secondary_dtm_dir = "./data/lhd_dir_gpao"
    output_dir = TMP_PATH / "gpao_run_without_cog_given_secondary_folder"
    output_dir.mkdir()
    project_name = "test_run_altianalysis_gpao_secondary_folder"

    gpao_hostname = os.environ.get("GPAO_API_URL", "localhost")
    url_api = f"http://{gpao_hostname}:8080/api/"

    runner_store_path = Path(dtm_lidar_lhds).resolve()
    local_store_path = Path("data/lhd_dir_gpao").resolve()

    run_difference_with_gpao.compute_on_gpao(
        Path(dtm_lidar_lhds),
        Path(secondary_dtm_dir),
        Path(output_dir),
        gpao_hostname,
        local_store_path,
        runner_store_path,
        project_name,
        cog_filename="",
    )

    if gpao_hostname == "localhost":
        tu.execute_gpao_client(tags="docker", num_thread=4)
    wait_running_job(url_api, project_name, delay_second=1, delay_log_second=10)

    assert (
        len([f for f in os.listdir(output_dir) if os.path.splitext(f)[-1] == ".tif"]) == 5
    )  # 5 individual output files + no cog
