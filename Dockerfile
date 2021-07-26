FROM continuumio/miniconda3:4.8.2

# Create the environment:
RUN mkdir /opt/app
COPY .binder/environment.yml /opt/app/environment.yml
RUN /opt/conda/bin/conda env update -f /opt/app/environment.yml

COPY prepare.sh /usr/bin/prepare.sh

ENTRYPOINT ["tini", "-g", "--", "/usr/bin/prepare.sh"]