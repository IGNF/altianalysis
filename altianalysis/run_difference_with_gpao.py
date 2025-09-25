import argparse
import logging
from pathlib import Path, PurePosixPath
from typing import List

from gpao.builder import Builder
from gpao.job import Job
from gpao.project import Project
from gpao_utils.store import Store

from altianalysis.version import __version__


def get_tile_names(folder: Path) -> List[str]:
    """Get tiles filenames from the content of a folder: tif or tiff or TIF files only

    Args:
        folder (Path): input folder

    Returns:
        List[str]: list of filenames
    """
    filenames = [f.name for f in folder.iterdir() if f.name.lower().endswith(("tif", "tiff", "TIF"))]

    return filenames


def create_one_job_one_difference(store: Store, dir_in: Path, second_dir: Path | None, input_file: str, output: Path):
    job_name = f"difference_{input_file}"
    if second_dir is not None:
        command = f"""
    docker run -t --rm --userns=host --shm-size=2gb
    -v {store.to_unix(dir_in)}:/input
    -v {store.to_unix(second_dir)}:/second_input
    -v {store.to_unix(output)}:/output
    ghcr.io/ignf/altianalysis:{__version__}
    python -m altianalysis.compute_difference
    --dtm_lidar_file /input/{input_file}
    --second_elevation_file /second_input/{input_file}
    --name_save_out /output/{input_file}
    """
    else:
        command = f"""
    docker run -t --rm --userns=host --shm-size=2gb
    -v {store.to_unix(dir_in)}:/input
    -v {store.to_unix(output)}:/output
    ghcr.io/ignf/altianalysis:{__version__}
    python -m altianalysis.compute_difference
    --dtm_lidar_file /input/{input_file}
    --name_save_out /output/{input_file}
    """
    job = Job(job_name, command, tags=["docker"])
    return job


def create_main_gpao_project(
    dtms_lhd: Path,
    secondary_dir: Path | None,
    out: Path,
    store: Store,
    project_name: str,
) -> Project:

    logging.debug(f"Create GPAO projects to compute difference maps with rge alti: {dtms_lhd}.")
    logging.debug(f"Writing difference maps to {out}.")

    Project.reset()

    # get dtm tile names for lidar hd

    dtm_tile_names = get_tile_names(dtms_lhd)

    out.mkdir(parents=True, exist_ok=True)

    # create individual jobs

    jobs = []

    for tile_ in dtm_tile_names:
        job = create_one_job_one_difference(store, dtms_lhd, secondary_dir, tile_, out)
        jobs.append(job)

    # create the project
    return Project(project_name, jobs)


def create_cog_gpao_project(
    input_dir: str,
    output_dir: str,
    store: Store,
    project_name=str,
    output_filename: str = "cog.tif",
    resampling: str = "CUBIC",
) -> Project:
    job_name = "create_cog"
    command = f"""
docker run --rm --userns=host
-v {store.to_unix(input_dir)}:/input
-v {store.to_unix(output_dir)}:/output
ghcr.io/ignf/altianalysis:{__version__}
bash -c 'ls -d /input/*.tif > cog_input_files.txt &&
gdalbuildvrt -input_file_list cog_input_files.txt vrt_output.vrt &&
gdal_translate \
    --config GDAL_DISABLE_READDIR_ON_OPEN TRUE \
    -co BIGTIFF=YES \
    -co RESAMPLING={resampling} \
    -co COMPRESS=LZW \
    -co PREDICTOR=YES \
    -of COG \
    vrt_output.vrt \
    /output/{output_filename}'
"""
    job = Job(job_name, command, tags=["docker"])
    project = Project(project_name, [job])

    return project


def create_gpao_projects(
    dtms_lhd: Path, secondary_dir: Path | None, out: Path, store: Store, project_name: str, cog_filename: str
) -> List[Project]:
    project_main = create_main_gpao_project(dtms_lhd, secondary_dir, out, store, project_name)
    projects = [project_main]
    if cog_filename:
        project_cog = create_cog_gpao_project(
            out, out, output_filename=cog_filename, store=store, project_name=f"{project_name}_cog"
        )
        project_cog.add_dependency(project_main)
        projects.append(project_cog)
    return projects


def compute_on_gpao(
    dtms_lhd: Path,
    secondary_dir: Path | None,
    out: Path,
    gpao_hostname: str,
    local_store_path: Path,
    runner_store_path: PurePosixPath,
    project_name: str,
    cog_filename: str = "",
):
    """Compute difference on all tif files of a folder, and optionally create a COG of the created difference files
    using GPAO for parallelization.
    If created, the output cog is saved in the same folder as the individual tif outputs

    Args:
        dtms_lhd (Path): folder containing the reference dtms
        out (Path): folder in which to save the output tils
        gpao_hostname (str): hostname of the gpao server
        local_store_path (Path): path on your computer to a common store between local computer and gpao runners
        runner_store_path (PurePosixPath): path on the gpao runners to a common store between local computer and gpao
        project_name (str): name to give to the main gpao project
        cog_filename (str): name of the cog file to create (no cog is generated if cog_filename is empty)
    """

    logging.debug(f"Use GPAO server: {gpao_hostname}")

    store = Store(local_store_path, unix_path=runner_store_path)

    logging.debug(f"Local store path ({local_store_path}) converted to client store path ({runner_store_path})")

    projects = create_gpao_projects(dtms_lhd, secondary_dir, out, store, project_name, cog_filename)

    builder = Builder(projects)

    builder.save_as_json(out / "gpao_project.json")

    logging.info(f"Send projects to gpao server: {gpao_hostname}")
    builder.send_project_to_api(f"http://{gpao_hostname}:8080")


def parse_args():
    parser = argparse.ArgumentParser(description="Calcul de cartes de différences par rapport au RGE ALTI")
    parser.add_argument(
        "-i",
        "--dtm_lhd_dir",
        type=Path,
        # nargs="+",
        required=True,
        help="Dossier des dalles MNT Lidar HD",
    )
    parser.add_argument(
        "-i",
        "--secondary_dtm_dir",
        type=Path,
        default=None,
        help="Dossier du second des MNT pour calculer la différence",
    )

    parser.add_argument(
        "-o",
        "--out",
        type=Path,
        required=True,
        help="Dossier de sortie où seront sauvegardées les cartes de differences",
    )

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
    parser.add_argument(
        "-c",
        "--cog_filename",
        type=str,
        help="Nom du fichier cog sauvé dans le même dossier que les sorties individuelles. "
        "Pas de cog généré si non renseigné",
        default="",
    )

    return parser.parse_args()


if __name__ == "__main__":
    logging.basicConfig(level="INFO")

    args = parse_args()

    compute_on_gpao(
        dtms_lhd=args.dtm_lhd_dir,
        secondary_dir=args.secondary_dtm_dir,
        out=args.out,
        gpao_hostname=args.gpao_hostname,
        local_store_path=args.local_store_path,
        runner_store_path=args.runner_store_path,
        project_name=args.project_name,
        cog_filename=args.cog_filename,
    )
