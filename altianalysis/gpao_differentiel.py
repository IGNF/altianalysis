import os, sys
from pathlib import Path, PurePosixPath
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
from joblib import Parallel, delayed
from typing import List

from gpao.builder import Builder
from gpao.project import Project
from gpao_utils.store import Store
from gpao.job import Job
from altianalysis.version import __version__
from altianalysis.gpao_utils import save_projects_as_json




def get_tile_names(folder: Path) -> List[str]:
    """Get tiles filenames from the content of a folder: tif or tiff or TIF files only

    Args:
        folder (Path): input folder

    Returns:
        List[str]: list of filenames
    """
    filenames = [f.name for f in folder.iterdir() if f.name.lower().endswith(("tif", "tiff", "TIF"))]

    return filenames



def create_one_job_one_difference(store: Store, dir_in: Path, input_file : str , output: Path):
    job_name = f"difference_{input_file}"
    command = f"""
docker run -t --rm --userns=host --shm-size=2gb
-v {store.to_unix(dir_in)}:/input
-v {store.to_unix(output)}:/output
ghcr.io/ignf/altianalysis:{__version__}
python -m altianalysis.calculDifferentiel 
--dtm_lidar_file /input/{input_file} 
--name_save_out /output/{input_file}
"""
    job = Job(job_name, command, tags=["docker"])
    return job




def create_gpao_project(
    dtms_lhd: Path,
    out: Path,
    store: Store,
    project_name: str,
) -> Project:
    
    logging.debug(
        f"Create GPAO projects to compute {len(dtms_lhd)} difference maps with rge alti: {dtms_lhd}."
    )
    logging.debug(f"Writing difference maps to {out}.")

    Project.reset()

    # get dtm tile names for lidar hd 

    dtm_tile_names=get_tile_names(dtms_lhd)

    out.mkdir(parents=True, exist_ok=True)

    # create individual jobs 
    
    jobs=[]

    for tile_ in dtm_tile_names:
        job=create_one_job_one_difference(store,
                                          dtms_lhd,
                                          tile_,
                                          out)
        jobs.append(job)

    # create the project
    return Project(project_name, jobs)



def parse_args():
    parser = argparse.ArgumentParser(description="Calcul de cartes de différences par rapport au RGE ALTI")
    parser.add_argument(
        "-i",
        "--dtm_lhd_dir",
        type=Path,
        nargs="+",
        required=True,
        help="Dossier des dalles MNT Lidar HD",
    )
    parser.add_argument("-o", "--out", type=Path, required=True, help="Dossier de sortie où seront sauvegardées les cartes de differences")

    parser.add_argument(
        "-l",
        "--local_store_path",
        type=Path,
        required=True,
        help="Chemin vers un store commun sur le PC qui lance ce script",
    )
    parser.add_argument(
        "-s",
        "--runner_store_path",
        type=PurePosixPath,
        help="Chemin vers un store commun sur les clients GPAO (Unix path)",
        required=True,
    )
    parser.add_argument("-g", "--gpao_hostname", type=str, help="Hostname du serveur GPAO", default="localhost")
    parser.add_argument("-p", "--project_name", type=str, default="altianalysis", help="Nom de projet pour la GPAO")

    return parser.parse_args()


def compute_on_gpao(
    dtms_lhd: Path,
    out: Path,
    gpao_hostname: str,
    local_store_path: Path,
    runner_store_path: PurePosixPath,
    project_name: str ):

    logging.debug(f"Use GPAO server: {gpao_hostname}")
    
    store = Store(local_store_path, unix_path=runner_store_path)
    
    logging.debug(f"Local store path ({local_store_path}) converted to client store path ({runner_store_path})")

    project = create_gpao_project(dtms_lhd, out, store, project_name)

    builder = Builder([project])
    logging.info(f"Send projects to gpao server: {gpao_hostname}")
    builder.send_project_to_api(f"http://{gpao_hostname}:8080")
    # Do not use builder.save_as_json because it resets projects/jobs ids.
    # cf https://github.com/ign-gpao/builder-python/issues/10
    save_projects_as_json([project], out / "gpao_project.json")

if __name__=="__main__":
    logging.basicConfig(level="INFO")

    args=parse_args()

    compute_on_gpao(args.dtm_lhd_dir,
                    args.out,
                    args.gpao_hostname,
                    args.local_store_path,
                    args.runner_store_path,
                    args.project_name
                    )