FROM continuumio/miniconda3

WORKDIR /usr/local
RUN git clone https://github.com/neurodata/ndviz.git
WORKDIR /usr/local/ndviz/python
COPY requirements.txt /tmp/requirements.txt 
RUN apt-get update && \
    apt-get install -y build-essential nginx supervisor && \
    conda install numpy && \
    pip install --upgrade pip && \
    pip install neuroglancer && \
    python setup.py install && \
    pip install flask && \
    pip install -r /tmp/requirements.txt && \
    apt-get remove -y build-essential && apt autoremove -y && \
    rm -rf /root/.cache && \
    rm -rf /var/lib/apt/lists/*
RUN conda update -n base conda
RUN conda install -c conda-forge uwsgi 

ENV SYNAPSEDB_SETTINGS /synapsedb/synapsedb/instance/dev_config.py


# Copy the Nginx global conf
COPY ./docker/nginx.conf /etc/nginx/
# Copy the Flask Nginx site conf
COPY ./docker/flask-site-nginx.conf /etc/nginx/conf.d/
# Copy the base uWSGI ini file to enable default dynamic uwsgi process number
COPY ./docker/uwsgi.ini /etc/uwsgi/
# Custom Supervisord config
COPY ./docker/supervisord.conf /etc/supervisord.conf

# Add demo app
COPY . /synapsedb
WORKDIR /synapsedb
RUN python setup.py install
RUN useradd -ms /bin/bash nginx
EXPOSE 80
CMD ["/usr/bin/supervisord","-c","/etc/supervisord.conf"]