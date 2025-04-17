MOUNT_DIR=/mnt/store-lidarhd

python -m altianalysis.main \
-i ${MOUNT_DIR}/production/chantiers/_LidarExpress/_dali/Sample \
-o ${MOUNT_DIR}/production/chantiers/_LidarExpress/_dali/SampleDiff \
-g smlqlidarhdap2 \
-l /mnt/store-lidarhd \
-s /var/data/store-lidarhd \
-p calcul_differentiel_test