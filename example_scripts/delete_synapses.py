from synapsedb import db
from synapsedb.volumes.models import Volume, DataSet
from synapsedb.synapses.models import Synapse, SynapseCollection

volume_name = "Take2Site5"
volume = Volume.query.filter_by(name=volume_name).first()

syn_colletions = SynapseCollection.query.filter_by(volume=volume).all()

for syncoll in syn_colletions:
    synapses = Synapse.query.filter_by(collection=syncoll).all()
    for synapse in synapses:
        print(synapse)
        db.session.delete(synapse)
db.session.commit()
