import json
import os
import shutil
from pathlib import Path

# import pytest
# import requests
# from client import worker
# from gpao.builder import Builder, Project
# from gpao_utils import gpao_test as gt
from gpao_utils.store import Store

import altianalysis.gpao_differentiel as gpao_differentiel

TMP_PATH = Path("./tmp/gpao_differentiel")

STORE = Store("local_store", "win_store", "unix_store")

URL_API = "http://localhost:8080/api/"


def setup_module(module):
    try:
        shutil.rmtree(TMP_PATH)
    except FileNotFoundError:
        pass
    os.makedirs(TMP_PATH)


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
