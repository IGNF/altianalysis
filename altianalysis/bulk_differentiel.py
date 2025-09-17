import argparse
import os
import tempfile
from pathlib import Path

from joblib import Parallel, delayed

from altianalysis.calcul_differentiel import _compute_difference_with_rge_alti, _extract_rge_alti_tile_from_stream


def _compute_one_difference(dtm_lhd_file: str, _dir: Path, _out_dir_difference: Path):

    full_dtm_file = os.path.join(_dir, dtm_lhd_file)
    full_difference_file = os.path.join(_out_dir_difference, dtm_lhd_file)

    # compute difference for individual files
    with tempfile.NamedTemporaryFile(suffix="_dtm_rgealti.tif", delete=False) as tmp_rge:

        success = _extract_rge_alti_tile_from_stream(full_dtm_file, tmp_rge.name)
        if success:
            _compute_difference_with_rge_alti(full_dtm_file, tmp_rge.name, full_difference_file)


def compute_all_difference_maps(_dir: Path, _out_dir_difference: Path):

    os.makedirs(_out_dir_difference, exist_ok=True)
    all_dtm_lhd_names = []

    for dtm_file in _dir.iterdir():
        if dtm_file.is_file() and (str(dtm_file).endswith(".tif") or str(dtm_file).endswith(".TIF")):
            all_dtm_lhd_names.append(dtm_file.name)

    # bulk compute
    _ = Parallel(n_jobs=12, verbose=True)(
        delayed(_compute_one_difference)(dtm_lhd_file, _dir, _out_dir_difference) for dtm_lhd_file in all_dtm_lhd_names
    )


def parse_args():
    parser = argparse.ArgumentParser(description="Calcul de cartes de différences par rapport au RGE ALTI")
    parser.add_argument(
        "-l",
        "--dtm_lidar_dir",
        type=Path,
        required=True,
        help="Dossier des dalles MNT Lidar HD",
    )
    parser.add_argument(
        "-o",
        "--name_dir_difference",
        type=Path,
        required=True,
        help="Dossier de sortie où seront sauvegardées les cartes de differences",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    compute_all_difference_maps(args.dtm_lidar_dir, args.name_dir_difference)
