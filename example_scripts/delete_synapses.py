from synapsedb import db
from synapsedb.volumes.models import Volume, DataSet
from synapsedb.synapses.models import Synapse, SynapseCollection

volume_name = "Site3"
name="glut_synapses_v51"
volume = Volume.query.filter_by(name=volume_name).first()

syncoll = SynapseCollection.query.filter_by(volume=volume,name=name).first()
synapses = Synapse.query.filter_by(collection=syncoll).all()
for synapse in synapses:
    print(synapse)
    db.session.delete(synapse)
db.session.delete(syncoll)
db.session.commit()
