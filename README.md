# alti analysis

Calcul altimétrique

*Ce projet est en cours de développement*

# Principe

L'objectif de ce projet est de calculer des différentiels entre les MNT LIDAR HD et le RGE ALTI

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

## Commande

Sous Windows : lancer `Miniforge Prompt`

Sous Linux : lancer un terminal

Dans les 2 cas :

Activer l'environnement conda :
```bash
conda activate altianalysis
```

Lancer l'utilitaire avec la commande suivante :

```bash
python -m altianalysis.calculDifferentiel -i <LHD>  \
                       -o <OUT> \
                       -g <GPAO_HOSTNAME> \
                       -l <LOCAL_STORE_PATH> \
                       -s <RUNNER_STORE_PATH> \
                       -p <PROJECT_NAME>
```

options:
*  -i INPUT [INPUT ...], --input INPUT [INPUT ...]
                        Dossier(s) contenant des dalles mnt Lidar HD.
*  -o OUT, --out OUT     Dossier de sortie des cartes de différence
*  -l LOCAL_STORE_PATH, --local-store-path LOCAL_STORE_PATH
                        Chemin vers un store commun sur le PC qui lance ce script
*  -s RUNNER_STORE_PATH, --runner-store-path RUNNER_STORE_PATH
                        Chemin vers un store commun sur les clients GPAO (Unix path)
*  -g GPAO_HOSTNAME, --gpao-hostname GPAO_HOSTNAME
                        Hostname du serveur GPAO
*  -p PROJECT_NAME, --project-name PROJECT_NAME
                        Nom de projet pour la GPAO




# Contribuer

Ce dépôt utiliser des pre-commits pour le formattage du code.
Avant de d'ajouter des changements, veillez à lancer `make install-precommit` pour installer les precommit hooks.

Pour lancer les tests : `make testing`
