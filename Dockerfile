FROM continuumio/miniconda3:4.8.2

# Create the environment:
COPY .binder/environment.yml .
RUN conda env create -f environment.yml

# Make RUN commands use the new environment:
SHELL ["conda", "run", "-n", "era5-forge", "/bin/bash", "-c"]

COPY prepare.sh /usr/bin/prepare.sh

RUN mkdir /opt/app

ENTRYPOINT ["tini", "-g", "--", "/usr/bin/prepare.sh"]