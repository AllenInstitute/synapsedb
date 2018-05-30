from synapsedb import db
from synapsedb.ratings.models import ClassificationType

gaba_type = ClassificationType(name='GABA')
synapse_type = ClassificationType(name='Synapse')
preRorb_type = ClassificationType(name='preRorb')
postRorb_type = ClassificationType(name='postRorb')
shaft_type = ClassificationType(name='shaft')
types = [gaba_type, synapse_type, preRorb_type, postRorb_type,shaft_type]
for t in types:
    db.session.add(t)

db.session.commit()
