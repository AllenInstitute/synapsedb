# synapsedb
A flask app for storing metadata about synapses

## Level of support
We are not currently supporting this code, but simply releasing it to the community AS IS but are not able to provide any guarantees of support.  The community is welcome to submit issues, but you should not expect an active response.

## Getting started
Install docker.

```
  # spin up a postgres database on your localhost
  docker-compose up -d
  pip install -r requirements.txt
  python setup.py install
  ./run_devserver.sh
```

navigate to http://localhost:5000/admin for admin interface

