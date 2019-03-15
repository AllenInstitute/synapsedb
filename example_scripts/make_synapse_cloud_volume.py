import argschema
from shapely import geometry
from geoalchemy2 import shape
from sqlalchemy.sql.expression import or_, any_
from sqlalchemy import func
from synapsedb import db
import cloudvolume
from synapsedb.synapses.postgis import ST_3DExtent
from synapsedb.synapses.controllers import get_box_as_array
from synapsedb.synapses.models import Synapse
from synapsedb.ratings.models import Rating, ClassificationType
import cv2
import numpy as np

example_parameters = {
    "synapse_collection_id": 2,
    "cv_for_bounds": "file:///nas3/data/M247514_Rorb_1/processed/Site3Align2Stacks/cv_Site3Align2_EM_clahe_mm",
    "cv_output": "file:///nas3/data/M247514_Rorb_1/processed/Site3Align2Stacks/cv_synapses"
}


class MaterializeSynapseLabelsParameters(argschema.ArgSchema):
    cv_for_bounds = argschema.fields.String(
        required=True, description="path to cloud volume to use for base metadata")
    cv_output = argschema.fields.String(
        required=True, description="path to cloud volume to save annotations into")
    synapse_collection_id = argschema.fields.Integer(
        required=True, description="id of synapse collection")


def reshape_xy(xy, minx, miny):
    xy = np.vstack(xy)
    xy = np.int64(xy.T)
    xy[:, 0] -= minx
    xy[:, 1] -= miny
    return np.copy(xy)

def paint_synapses_to_vol(vol, synapses):
    for synapse in synapses:
        print(synapse.id)
        multPolygon = shape.to_shape(synapse.areas)
        for poly in multPolygon.geoms:
            exterior = poly.exterior
            z = int(exterior.coords[0][2])
            (minx, miny, maxx, maxy) = poly.bounds
            minx=int(minx)
            miny=int(miny)
            maxx=int(maxx)
            maxy=int(maxy)
            label_patch = np.zeros(
                (maxy- miny+ 1, maxx - minx + 1), dtype=np.uint8)
            path = reshape_xy(exterior.xy, minx, miny)
            #print(label_patch.shape)dd
            #print(path)
            label_patch = cv2.fillPoly(
                label_patch, [path], 1)

            for interior in poly.interiors:
                path = reshape_xy(interior.xy, minx, miny)
                label_patch = cv2.fillPoly(
                    label_patch, [path], 0)
            a=vol[minx:maxx+1, miny:maxy+1, z,0]
            #print(label_patch.shape)
            #print(a.shape)
            inc = np.uint64(label_patch.T)*synapse.id
            a[:,:,0,0]+=inc
            vol[minx:maxx+1, miny:maxy+1, z,0] = a


class MaterializeSynapseLabels(argschema.ArgSchemaParser):
    default_schema = MaterializeSynapseLabelsParameters

    def run(self):
        collection_id = self.args['synapse_collection_id']
       
        box = Synapse.query.with_entities(ST_3DExtent(Synapse.areas))\
            .filter_by(object_collection_id=collection_id).first()[0]
        bounds = np.array(get_box_as_array(box))
        mins = bounds[0:3]
        maxs = bounds[3:]
        print(mins)
        print(maxs)

        cv = cloudvolume.CloudVolume(self.args['cv_for_bounds'], mip=0, compress=True)
        info = cv._fetch_info()
        info['type']='segmentation'
        info['encoding']='compressed_segmentation'
        info['data_type']='uint64'


        newinfo = cloudvolume.CloudVolume.create_new_info(
            num_channels    = 1,
            layer_type      = 'segmentation',
            data_type       = 'uint64', # Channel images might be 'uint8'
            encoding        = 'raw', # raw, jpeg, compressed_segmentation are all options
            resolution      = info['scales'][0]['resolution'], # Voxel scaling, units are in nanometers
            voxel_offset    = info['scales'][0]['voxel_offset'], # x,y,z offset in voxels from the origin
            mesh            = 'mesh',
            # Pick a convenient size for your underlying chunk representation
            # Powers of two are recommended, doesn't need to cover image exactly
            chunk_size      = info['scales'][0]['chunk_sizes'][0], # units are voxels
            volume_size     = info['scales'][0]['size'], # e.g. a cubic millimeter dataset
        )
        #print(newinfo)
        cv_out = cloudvolume.CloudVolume(self.args['cv_output'], mip=0,
                                         info=newinfo, fill_missing=True, non_aligned_writes=True)
        cv_out.commit_info()

        synapses = Synapse.query.filter_by(object_collection_id=collection_id).all()

        #paint_synapses_to_vol(cv_out, synapses)
        


if __name__ == '__main__':
    mod = MaterializeSynapseLabels(input_data=example_parameters)
    mod.run()
