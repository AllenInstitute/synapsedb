from synapsedb.synapses.models import SynapseCollection, Synapse, SYNAPSE_SRID
from synapsedb.volumes.models import Volume, DataSet
from synapsedb import db
import json
import numpy as np
from shapely import geometry
from geoalchemy2.shape import from_shape
import argschema

example_parameters = {
    "dataset": "M247514_Rorb_1",
    "volume": "Take2Site4",
    "synapse_collection_name": "EM Synapses",
    "synapse_collection_type": "manual annotation",
    "synapse_file": "/nas3/data/M247514_Rorb_1/annotation/m247514_Take2Site4Annotation_MN_Take2Site4global.json"
}


class SynapseUploadParameters(argschema.ArgSchema):
    dataset = argschema.fields.String(
        required=True, description="name of dataset")
    volume = argschema.fields.String(
        required=True, description="name of volume in dataset")
    synapse_file = argschema.fields.InputFile(
        required=True, description="global synapse json file path")
    synapse_collection_name = argschema.fields.String(
        required=True,
        default="EM Synapses",
        description="name of synapse collection"
    )
    synapse_collection_type = argschema.fields.String(
        required=True, default='manual annotation',
        description="string describing synapse collection type")


class SynapseUpload(argschema.ArgSchemaParser):
    default_schema = SynapseUploadParameters

    def run(self):

        dataset = DataSet.query.filter_by(name=self.args['dataset']).first()
        volume = Volume.query.filter_by(name=self.args['volume'],
                                        dataset=dataset).first()

        coll_type = self.args['synapse_collection_type']
        coll_name = self.args['synapse_collection_name']
        collection = SynapseCollection(name=coll_name,
                                       volume=volume,
                                       synapse_collection_type=coll_type
                                       )

        synapse_file = self.args['synapse_file']
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


if __name__ == '__main__':
    mod = SynapseUpload(input_data=example_parameters, args=[])
    mod.run()
