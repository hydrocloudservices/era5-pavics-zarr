FROM continuumio/miniconda3:4.8.2

# Create the environment:
RUN mkdir /opt/app
COPY .binder/environment.yml /opt/app/environment.yml
RUN /opt/conda/bin/conda env update -f /opt/app/environment.yml

# Make RUN commands use the new environment:
SHELL ["conda", "run", "-n", "era5-forge", "/bin/bash", "-c"]

COPY prepare.sh /usr/bin/prepare.sh


ENTRYPOINT ["tini", "-g", "--", "/usr/bin/prepare.sh"]