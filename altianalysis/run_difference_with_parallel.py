import argparse
import os
from pathlib import Path

from joblib import Parallel, delayed

from altianalysis.compute_difference import main


def _compute_one_difference(dtm_file: str, _dir: Path, _out_dir_difference: Path, second_dir=None):

    full_dtm_file = os.path.join(_dir, dtm_file)
    full_difference_file = os.path.join(_out_dir_difference, dtm_file)
    second_file = None

    if second_dir:
        second_file = os.path.join(second_dir, dtm_file)

    main(full_dtm_file, second_file, full_difference_file)


def compute_all_difference_maps(dir: Path, second_dir: Path | None, out_dir_difference: Path):

    os.makedirs(out_dir_difference, exist_ok=True)
    all_dtm_names = []
    for dtm_file in dir.iterdir():
        if dtm_file.is_file() and (str(dtm_file).endswith(".tif") or str(dtm_file).endswith(".TIF")):
            all_dtm_names.append(dtm_file.name)

    # bulk compute
    _ = Parallel(n_jobs=12, verbose=True)(
        delayed(_compute_one_difference)(dtm_file, dir, out_dir_difference, second_dir=second_dir)
        for dtm_file in all_dtm_names
    )


def parse_args():
    parser = argparse.ArgumentParser(description="Calcul de cartes de différences par rapport au RGE ALTI")
    parser.add_argument(
        "-l",
        "--primary_dtm_dir",
        type=Path,
        required=True,
        help="Dossier contenant le premier ensemble de dalles MNT pour le calcul de différence.",
    )

    parser.add_argument(
        "-s",
        "--secondary_dtm_dir",
        type=Path,
        default=None,
        help="Dossier contenant le second ensemble de dalles MNT pour le calcul de différence. "
        "Les dalles d'élévation doivent avoir les mêmes noms pour faire l'appariement"
        "S'il est laissé vide, les dalles du premier ensemble sont comparées au RGE Alti",
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
    compute_all_difference_maps(args.primary_dtm_dir, args.secondary_dtm_dir, args.name_dir_difference)
