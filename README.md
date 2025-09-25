# alti analysis

Calcul altimétrique

*Ce projet est en cours de développement*

# Principe

L'objectif de ce projet est de calculer des différentiels entre :
- les MNT LIDAR HD (stockés localement sous forme de fichiers .tif)
- le produit [RGE ALTI](https://geoservices.ign.fr/rgealti) récupéré via les flux de diffusions de la [geoplateforme](https://geoservices.ign.fr/services-geoplateforme-diffusion).

Ce projet utilise une infrastructure de gestion de production par ordinateur [IGN GPAO](https://github.com/ign-gpao)
développée au sein de l'IGNF pour la parallélisation des calculs.


# Installation

Ce code utilise mamba pour l'installation de l'environnement python (et suppose qu'une version de mamba ou micromamba
existe sur l'ordinateur sur lequel on veut installer le programme)

Pour installer micromamba, voir https://mamba.readthedocs.io/en/latest/micromamba-installation.html#umamba-install

Sous windows :
* lancer `Miniforge Prompt`
* y exectuer `install_or_update.bat`

Sous linux :
* lancer un terminal
* y executer `make install`

# Usage

## Activation de l'environnement

Sous Windows : lancer `Miniforge Prompt`

Sous Linux : lancer un terminal

Dans les 2 cas :

Activer l'environnement conda :
```bash
conda activate altianalysis
```

## Utilisation sur un seul fichier tif

Lancer l'utilitaire avec la commande suivante :

```bash
python -m altianalysis.compute_difference \
    --dtm_lidar_file <DTM_LIDAR_FILE> \
    --name_save_out <NAME_SAVE_OUT>
```

options:
  * --dtm_lidar_file DTM_LIDAR_FILE
                        Chemin vers in fichier tif pour lequel on veut calculer la différence avec le RGE Alti
  * --name_save_out NAME_SAVE_OUT
                        Chemin vers le fichier tif de sortie (carte de différence)



## Utilisation pour un batch en utilisant la [GPAO](https://github.com/ign-gpao/)

Lancer l'utilitaire avec la commande suivante :

```bash
python -m altianalysis.run_difference_with_gpao \
    -i <DTM_LHD_DIR> \
    -o <OUT> \
    -l <LOCAL_STORE_PATH> \
    -s <RUNNER_STORE_PATH> \
    [-g <GPAO_HOSTNAME>] \
    [-p <PROJECT_NAME>] \
    [-c <COG_FILENAME>]
```

options:
  * -h, --help            show this help message and exit
  * -i DTM_LHD_DIR, --dtm_lhd_dir DTM_LHD_DIR
                        Dossier des dalles MNT Lidar HD
  * -o OUT, --out OUT     Dossier de sortie où seront sauvegardées les cartes de
                        differences
  * -l LOCAL_STORE_PATH, --local_store_path LOCAL_STORE_PATH
                        Chemin vers un store commun sur le PC qui lance ce
                        script
  * -s RUNNER_STORE_PATH, --runner_store_path RUNNER_STORE_PATH
                        Chemin vers un store commun sur les clients GPAO (Unix
                        path)
  * -g GPAO_HOSTNAME, --gpao_hostname GPAO_HOSTNAME
                        Hostname du serveur GPAO
  * -p PROJECT_NAME, --project_name PROJECT_NAME
                        Nom de projet pour la GPAO
  * -c COG_FILENAME, --cog_filename COG_FILENAME
                        Nom du fichier cog sauvé dans le même dossier que les
                        sorties individuelles. Pas de cog généré si non
                        renseigné


# Contribuer

Ce dépôt utilise des pre-commits pour le formattage du code.
Avant de d'ajouter des changements, veillez à lancer `make install-precommit` pour installer les precommit hooks.

Pour lancer les tests : `make testing`
