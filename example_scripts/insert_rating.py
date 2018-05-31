from synapsedb import db
from synapsedb.volumes.models import DataSet, Volume
from synapsedb.ratings.models import ClassificationType, BinaryRating, ConsensusSource
from synapsedb.synapses.models import Synapse, SynapseCollection
import pandas as pd
import numpy as np

gaba_type = ClassificationType.query.filter_by(name='GABA').first()
synapse_type = ClassificationType.query.filter_by(name='Synapse').first()
preRorb_type = ClassificationType.query.filter_by(name='preRorb').first()
postRorb_type = ClassificationType.query.filter_by(name='postRorb').first()
shaft_type = ClassificationType.query.filter_by(name='shaft').first()
print(gaba_type, synapse_type, preRorb_type, postRorb_type, shaft_type)

dataset = DataSet.query.filter_by(name='M247514_Rorb_1').first()
volume = Volume.query.filter_by(name='Site3', dataset=dataset).first()

metadata_csv = "https://docs.google.com/spreadsheets/d/1cV6BuQosLgjZX1e2l9EZHTOSLZGlDETKjlv2-wjpeIk/export?gid=607779864&format=csv"
df = pd.read_csv(metadata_csv, index_col=0,
                 skiprows=1, dtype={'oid': np.object})


consensus_source = ConsensusSource(name="Site3ConsensusRatings")
db.session.add(consensus_source)
syncoll = SynapseCollection.query.filter_by(volume=volume,
                                            name='EM Synapses').first()

print(syncoll)
for k, row in df.iterrows():
    synapse = Synapse.query.filter_by(collection=syncoll, oid=row.oid).first()
    isGaba = (row.GABA == 1)
    gaba_rating = BinaryRating(object_id=synapse.id,
                               rating_source=consensus_source,
                               classificationtype=gaba_type,
                               bool_rating=isGaba)
    db.session.add(gaba_rating)
    issyn = (row.NotSynapse != 1)
    synapse_rating = BinaryRating(object_id=synapse.id,
                                  rating_source=consensus_source,
                                  classificationtype=synapse_type,
                                  bool_rating=issyn)
    db.session.add(synapse_rating)
    isShaft = (row.shaft == 0)
    shaft_rating = BinaryRating(object_id=synapse.id,
                                rating_source=consensus_source,
                                classificationtype=shaft_type,
                                bool_rating=isShaft)
    db.session.add(shaft_rating)

    isPre = (row.tdTom == 1) or (row.tdTom == 3)
    isPost = (row.tdTom == 2) or (row.tdTom == 3)
    preRorb_rating = BinaryRating(object_id=synapse.id,
                                  rating_source=consensus_source,
                                  classificationtype=preRorb_type,
                                  bool_rating=isPre)
    postRorb_rating = BinaryRating(object_id=synapse.id,
                                   rating_source=consensus_source,
                                   classificationtype=postRorb_type,
                                   bool_rating=isPost)
    # print(isGaba,issyn,isShaft,isPre,isPost)

    db.session.add(preRorb_rating)
    db.session.add(postRorb_rating)
    # break
db.session.commit()
