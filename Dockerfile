FROM mambaorg/micromamba:latest as mamba_pdal
COPY environment.yml /environment.yml
USER root
RUN micromamba env create -n altianalysis -f /environment.yml


FROM debian:bullseye-slim

# install PDAL
COPY --from=mamba_pdal /opt/conda/envs/altianalysis/bin/python /opt/conda/envs/altianalysis/bin/python
COPY --from=mamba_pdal /opt/conda/envs/altianalysis/lib/ /opt/conda/envs/altianalysis/lib/
COPY --from=mamba_pdal /opt/conda/envs/altianalysis/ssl /opt/conda/envs/altianalysis/ssl
COPY --from=mamba_pdal /opt/conda/envs/altianalysis/share/proj/proj.db /opt/conda/envs/altianalysis/share/proj/proj.db

ENV PATH=$PATH:/opt/conda/envs/altianalysis/bin/
ENV PROJ_LIB=/opt/conda/envs/altianalysis/share/proj/

WORKDIR /altianalysis
RUN mkdir tmp
COPY altianalysis altianalysis
COPY test test

# Copy test data that are stored directly in the altianalysis repository
COPY data/lhd data/lhd
COPY data/lhd_dir_gpao  data/lhd_dir_gpao
