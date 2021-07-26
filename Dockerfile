FROM continuumio/miniconda3:4.8.2

RUN conda install --yes \
    -c conda-forge \
    python==3.8 \
    python-blosc \
    cytoolz \
    dask==2021.7.1 \
    lz4 \
    nomkl \
    tini==0.18.0 \
    && conda clean -tipsy \
    && find /opt/conda/ -type f,l -name '*.a' -delete \
    && find /opt/conda/ -type f,l -name '*.pyc' -delete \
    && find /opt/conda/ -type f,l -name '*.js.map' -delete \
    && find /opt/conda/lib/python*/site-packages/bokeh/server/static -type f,l -name '*.js' -not -name '*.min.js' -delete \
    && rm -rf /opt/conda/pkgs

COPY prepare.sh /usr/bin/prepare.sh

RUN mkdir /opt/app

COPY .binder/environment.yml /opt/app/environment.yml

ENTRYPOINT ["tini", "-g", "--", "/usr/bin/prepare.sh"]