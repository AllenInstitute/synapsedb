#! /bin/bash 
export FLASK_APP=run.py
export FLASK_ENV=development
export SYNAPSEDB_SETTINGS=/pipeline/synapsedb/prod_config.py
flask run --host=0.0.0.0 --port=5000

