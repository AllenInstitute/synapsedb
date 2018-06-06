from synapsedb.synapses.models import SynapseCollection, Synapse, SYNAPSE_SRID
from synapsedb.volumes.models import Volume, DataSet
from synapsedb import db
import json
import numpy as np
from shapely import geometry
from geoalchemy2.shape import from_shape
import argschema
import pandas as pd

example_parameters = {
    "dataset": "M247514_Rorb_1",
    "volume": "Site3",
    "synapse_collection_name": "EM Synapses",
    "synapse_collection_type": "manual annotation",
    "synapse_file": "/nas3/data/M247514_Rorb_1/annotation/m247514_Site3Annotation_MN_global_Site3Align2_v2.json",
    "bounding_box_file": "/nas3/data/M247514_Rorb_1/annotation/m247514_Site3Annotation_MN_bb_Site3Align2_global.json"
}


class NegativeSynapseUploadParameters(argschema.ArgSchema):
    dataset = argschema.fields.String(
        required=True, description="name of dataset")
    volume = argschema.fields.String(
        required=True, description="name of volume in dataset")
    synapse_file = argschema.fields.InputFile(
        required=True, description="global synapse json file path")
    bounding_box_file = argschema.fields.InputFile(
        required=True, description="bounding box file path"
    )

    synapse_collection_name = argschema.fields.String(
        required=True,
        default="EM Synapses",
        description="name of synapse collection"
    )
    synapse_collection_type = argschema.fields.String(
        required=True, default='manual annotation',
        description="string describing synapse collection type")


def ann_to_df(anns):
    ds = []
    for ann in anns:
        for area in ann['areas']:
            d = area
            d['oid'] = ann['oid']
            ds.append(d)
    return pd.DataFrame(ds)


def make_path_from_area(global_path, z):
    path = np.array(global_path)
    path = np.concatenate(
        (path, z * np.ones((path.shape[0], 1))),
        axis=1)
    return path


class NegativeSynapseUpload(argschema.ArgSchemaParser):
    default_schema = NegativeSynapseUploadParameters

    def run(self):

        dataset = DataSet.query.filter_by(name=self.args['dataset']).first()
        volume = Volume.query.filter_by(name=self.args['volume'],
                                        dataset=dataset).first()

        coll_type = self.args['synapse_collection_type']
        coll_name = self.args['synapse_collection_name']
        collection = SynapseCollection.query.filter_by(name=coll_name,
                                                       volume=volume
                                                       ).first()

        synapse_file = self.args['synapse_file']
        with open(synapse_file, 'r') as fp:
            syn_anns = json.load(fp)

        bounding_box_filepath = self.args['bounding_box_file']
        with open(bounding_box_filepath, 'r') as fp:
            bb_anns = json.load(fp)

        bb_anns = bb_anns['area_lists']
        syn_anns = syn_anns['area_lists']

        syn_df = ann_to_df(syn_anns)
        bb_df = ann_to_df(bb_anns)

        polys = []
        for z, group in bb_df.groupby('z'):
            outer_path = group['global_path'].iloc[0]
            syn_subset_df = syn_df[syn_df['z'] == z]
            inner_paths = [make_path_from_area(
                row.global_path, row.z) for k, row in syn_subset_df.iterrows()]
            outer_path = make_path_from_area(outer_path, z)
            polys.append(geometry.Polygon(outer_path, inner_paths))
        mpoly = geometry.MultiPolygon(polys)

        syn = Synapse(oid='negative_synapse',
                      areas=from_shape(mpoly, srid=SYNAPSE_SRID),
                      collection=collection)
        db.session.add(syn)

        # db.session.add(collection)

        db.session.commit()


if __name__ == '__main__':
    mod = NegativeSynapseUpload(input_data=example_parameters, args=[])
    mod.run()
