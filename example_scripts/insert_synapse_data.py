from synapsedb.synapses.models import SynapseCollection, Synapse, SYNAPSE_SRID
from synapsedb.volumes.models import Volume, DataSet
from synapsedb import db
import json
import numpy as np
from shapely import geometry
from geoalchemy2.shape import from_shape

collections = SynapseCollection.query.all()
for coll in collections:
    db.session.delete(coll)

dataset = DataSet.query.filter_by(name='M247514_Rorb_1')[0]
volume = Volume.query.filter_by(name='Site3', dataset=dataset)[0]
print(volume)

collection = SynapseCollection(name='EM Synapses',
                               volume=volume,
                               synapse_collection_type='manual annotation'
                               )

synapse_file = 'm247514_Site3Annotation_MN_global_Site3Align2_v2.json'
with open(synapse_file, 'r') as fp:
    syn_anns = json.load(fp)

syn_anns = syn_anns['area_lists']
for ann in syn_anns:
    rings = []
    for area in ann['areas']:
        path = np.array(area['global_path'])
        path = np.concatenate(
            (path, area['z'] * np.ones((path.shape[0], 1))),
            axis=1)
        rings.append(geometry.Polygon(path))
    mpoly = geometry.MultiPolygon(rings)
    syn = Synapse(oid=ann['oid'],
                  areas=from_shape(mpoly, srid=SYNAPSE_SRID),
                  collection=collection)
    db.session.add(syn)


db.session.add(collection)

db.session.commit()
