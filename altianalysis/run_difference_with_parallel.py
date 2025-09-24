import argparse
import os
from pathlib import Path

from joblib import Parallel, delayed

from altianalysis.compute_difference import main


def _compute_one_difference(dtm_lhd_file: str, _dir: Path, _out_dir_difference: Path, second_dir=None):

    full_dtm_file = os.path.join(_dir, dtm_lhd_file)
    full_difference_file = os.path.join(_out_dir_difference, dtm_lhd_file)
    _second_file = None

    if second_dir is not None:
        _second_file = os.path.join(second_dir, dtm_lhd_file)

    main(full_dtm_file, _second_file, full_difference_file)


def compute_all_difference_maps(_dir: Path, _second_dir: Path | None, _out_dir_difference: Path):

    os.makedirs(_out_dir_difference, exist_ok=True)
    all_dtm_lhd_names = []
    for dtm_file in _dir.iterdir():
        if dtm_file.is_file() and (str(dtm_file).endswith(".tif") or str(dtm_file).endswith(".TIF")):
            all_dtm_lhd_names.append(dtm_file.name)

    # bulk compute
    _ = Parallel(n_jobs=12, verbose=True)(
        delayed(_compute_one_difference)(dtm_lhd_file, _dir, _out_dir_difference, second_dir=_second_dir)
        for dtm_lhd_file in all_dtm_lhd_names
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
        "-s",
        "--secondary_dtm_elevation_dir",
        type=Path,
        default=None,
        help="Dossier contenant le second ensemble de dalles MNT pour le calcul de différence",
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
    compute_all_difference_maps(args.dtm_lidar_dir, args.secondary_dtm_elevation_dir, args.name_dir_difference)
