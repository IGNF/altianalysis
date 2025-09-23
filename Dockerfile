FROM mambaorg/micromamba:latest AS mamba_pdal
COPY environment.yml /environment.yml
USER root
RUN micromamba env create -n altianalysis -f /environment.yml


FROM debian:bullseye-slim

# install PDAL
COPY --from=mamba_pdal /opt/conda/envs/altianalysis/bin/python /opt/conda/envs/altianalysis/bin/python
COPY --from=mamba_pdal /opt/conda/envs/altianalysis/lib/ /opt/conda/envs/altianalysis/lib/
COPY --from=mamba_pdal /opt/conda/envs/altianalysis/ssl /opt/conda/envs/altianalysis/ssl
COPY --from=mamba_pdal /opt/conda/envs/altianalysis/share/proj/proj.db /opt/conda/envs/altianalysis/share/proj/proj.db

# install gdal command line tools
COPY --from=mamba_pdal /opt/conda/envs/altianalysis/bin/*gdal* /opt/conda/envs/altianalysis/bin/

ENV PATH=$PATH:/opt/conda/envs/altianalysis/bin/
ENV PROJ_LIB=/opt/conda/envs/altianalysis/share/proj/

WORKDIR /altianalysis
RUN mkdir tmp
COPY altianalysis altianalysis
COPY test test
# Copy pyproject to register pytest markers
COPY pyproject.toml pyproject.toml

# Copy test data that are stored directly in the altianalysis repository
COPY data/lhd data/lhd
COPY data/lhd_dir_gpao  data/lhd_dir_gpao
