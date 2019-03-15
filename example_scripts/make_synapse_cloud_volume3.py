import argschema
from shapely import geometry
from geoalchemy2 import shape
from sqlalchemy.sql.expression import or_, any_
from sqlalchemy import func
from synapsedb import db
import cloudvolume
from synapsedb.synapses.postgis import ST_3DExtent, ST_XMin, ST_YMin, ST_ZMin, ST_ZMax, ST_XMax, ST_YMax
from synapsedb.synapses.postgis import ST_3DMakeBox, ST_MakePoint
from synapsedb.synapses.controllers import get_box_as_array
from synapsedb.synapses.models import Synapse
from synapsedb.ratings.models import Rating, ClassificationType
import cv2
import numpy as np
import itertools
from functools import partial
from pathos.multiprocessing import ProcessingPool as Pool

example_parameters = {
    "synapse_collection_id": 2,
    "rating_source_id": 24,
    "cv_for_bounds": "file:///nas3/data/M247514_Rorb_1/processed/Site3Align2Stacks/cv_Site3Align2_EM_clahe_mm",
    "cv_output": "file:///nas3/data/M247514_Rorb_1/processed/Site3Align2Stacks/cv_synapses",
    "cv_mask": "file:///nas3/data/M247514_Rorb_1/processed/Site3Align2Stacks/cv_mask",
    "rating_conditions": [
        {
            "classification_type": "Synapse",
            "rating": True
        }]
}


class RatingRequirements(argschema.schemas.DefaultSchema):
    classification_type = argschema.fields.String(
        required=True, description="name of classification type")
    rating = argschema.fields.Raw(
        required=True, description="rating that should be returned")


class MaterializeSynapseSparseGroundTruthParameters(argschema.ArgSchema):
    cv_for_bounds = argschema.fields.String(
        required=True, description="path to cloud volume to use for base metadata")
    cv_output = argschema.fields.String(
        required=True, description="path to cloud volume to save annotations into")
    cv_mask = argschema.fields.String(
        required=True, description="path to cloud volume to save mask region into")
    synapse_collection_id = argschema.fields.Integer(
        required=True, description="id of synapse collection")
    rating_source_id = argschema.fields.Integer(
        required=True, description="id of rating source to use")
    rating_conditions = argschema.fields.Nested(RatingRequirements,
                                                many=True,
                                                description="what ratings this synapse must have to be included")


def get_all_relevant_ratings_query(collection_id, rating_source_id, filters):
    # get all the synapses in this collection
    synapse_query = Synapse.query.filter_by(object_collection_id=collection_id)
    # filter the Ratings on those synapses that meet one of the filters
    # then grouped by synapse, so you can count how many conditions each passed
    rating_query = synapse_query.join(Rating, Rating.object_id == Synapse.id)\
        .with_entities(Synapse, func.count(Synapse.id))\
        .filter(Rating.rating_source_id == rating_source_id)\
        .filter(or_(*filters))\
        .group_by(Synapse.id)
    return rating_query


def get_has_any_rating_query(collection_id, rating_source_id, filters):
    # a grouped query for all the relevant ratings that passed one of the filters
    base_query = get_all_relevant_ratings_query(
        collection_id, rating_source_id, filters)
    # return those that have any of the relevant ratings
    return base_query.having(func.count(Rating.object_id) > 0)


def get_has_all_rating_query(collection_id, rating_source_id, filters):
    # a grouped query for all the relevant ratings that passed one of the filters
    base_query = get_all_relevant_ratings_query(
        collection_id, rating_source_id, filters)
    # return those that have any all the relevant ratings
    return base_query.having(func.count(Rating.object_id) == len(filters))


def make_chunk_box(mins, maxs):
    minpt = ST_MakePoint(*mins)
    maxpt = ST_MakePoint(*maxs)
    box3d = ST_3DMakeBox(minpt, maxpt)
    return box3d


def filter_query_by_bounding_box(base_query,
                                 mins, maxs):
    box3d = make_chunk_box(mins, maxs)
    return base_query.filter(Synapse.areas.intersects(box3d))


def construct_filters(rating_condition):
    type_lookup = {
        "BinaryRating": "bool_rating",
        "TertiaryRating": "tert_rating"
    }
    # get the classification type for this rating condition
    class_type = ClassificationType.query.filter_by(
        name=rating_condition['classification_type']).first()
    assert(class_type is not None)

    # get the column where the rating is stored
    rating_col = getattr(Rating, type_lookup[class_type.rating_type])

    # construct the condition that this rating is what it should be
    filter = (rating_col == rating_condition['rating']) &\
        (Rating.classificationtype == class_type)

    # and that this rating is not what it should be
    inverse_filter = (rating_col != rating_condition['rating']) &\
        (Rating.classificationtype == class_type)
    return (filter, inverse_filter)


def bound_box_3d(multPolygon):
    (xmin, ymin, xmax, ymax) = multPolygon.bounds
    xmin = int(xmin)
    ymin = int(ymin)
    ymax = int(ymax)
    xmax = int(xmax)
    zvals = np.array([int(poly.exterior.coords[0][2])
                      for poly in multPolygon.geoms])
    zmin = np.min(zvals)
    zmax = np.max(zvals)
    return (xmin, ymin, zmin, xmax, ymax, zmax)


def paint_synapses(label, synapses, mins, patch_size):
    xmin = mins[0]
    ymin = mins[1]
    zmin = mins[2]
    maxs = mins + patch_size
    xmax = maxs[0]
    ymax = maxs[1]
    zmax = maxs[2]
    new_patch_size = np.flip(np.array(patch_size), axis=0)

    tot_patch = np.zeros(patch_size, np.uint64)
    for synapse, count in synapses:
        patch = np.zeros(new_patch_size, np.uint8)
        multPolygon = shape.to_shape(synapse.areas)

        for poly in multPolygon.geoms:
            exterior = poly.exterior
            z = int(exterior.coords[0][2])
            zp = z - zmin
            if (zp >= 0) and (zp < patch_size[2]):
                path = (exterior.xy - mins[0:2, np.newaxis])
                patch[zp, :, :] = cv2.fillPoly(
                    patch[zp, :, :], [np.int64(path.T)], 1)

                for interior in poly.interiors:
                    path = (interior.xy - mins[0:2, np.newaxis])

                    patch[zp, :, :] = cv2.fillPoly(
                        patch[zp, :, :], [np.int64(path.T)], 0)
        patch = np.transpose(patch, [2, 1, 0])
        inc = np.uint64(patch) * synapse.id
        tot_patch += inc

    label[xmin:xmax, ymin:ymax, zmin:zmax] = tot_patch


def define_base_query(conditions, collection_id, rating_source_id):
    filters = []
    for rating_condition in conditions:
        filter, inverse_filter = construct_filters(rating_condition)
        filters.append(filter)

    rating_query = get_has_all_rating_query(
        collection_id, rating_source_id, filters)
    return rating_query


def paint_synapses_in_box(conditions, collection_id, rating_source_id,
                          cv_path, patch_size, mins):

    base_query = define_base_query(conditions, collection_id, rating_source_id)
    maxs = np.array(mins) + np.array(patch_size)
    new_query = filter_query_by_bounding_box(base_query, mins, maxs)
    if new_query.count() > 0:
        vol = cloudvolume.CloudVolume(cv_path, mip=0, fill_missing=True)
        paint_synapses(vol, new_query.all(), np.array(
            mins), np.array(patch_size))


class MaterializeSynapseSparseGroundTruth(argschema.ArgSchemaParser):
    default_schema = MaterializeSynapseSparseGroundTruthParameters

    def run(self):
        collection_id = self.args['synapse_collection_id']
        rating_source_id = self.args['rating_source_id']

        cv = cloudvolume.CloudVolume(
            self.args['cv_for_bounds'], mip=0, compress=True)
        info = cv._fetch_info()
        volume_size = info['scales'][0]['size']
        chunk_size = info['scales'][0]['chunk_sizes'][0]
        voxel_offset = info['scales'][0]['voxel_offset']
        seginfo = cloudvolume.CloudVolume.create_new_info(
            num_channels=1,
            layer_type='segmentation',
            data_type='uint64',  # Channel images might be 'uint8'
            encoding='raw',  # raw, jpeg, compressed_segmentation are all options
            # Voxel scaling, units are in nanometers
            resolution=info['scales'][0]['resolution'],
            # x,y,z offset in voxels from the origin
            voxel_offset=voxel_offset,
            mesh='mesh',
            # Pick a convenient size for your underlying chunk representation
            # Powers of two are recommended, doesn't need to cover image exactly
            chunk_size=chunk_size,  # units are voxels
            # e.g. a cubic millimeter dataset
            volume_size=volume_size,
        )

        cv_seg = cloudvolume.CloudVolume(self.args['cv_output'], mip=0,
                                         info=seginfo, fill_missing=True)
        cv_seg.commit_info()

        box = Synapse.query.with_entities(ST_3DExtent(Synapse.areas))\
            .filter_by(object_collection_id=collection_id).first()
        


        steps = list()
        for start, dim, dim_step, patch in zip(voxel_offset,
                                               volume_size,
                                               chunk_size,
                                               chunk_size):
            # make sure we get a _full_ patch for the last sample
            starts = np.hstack(
                [np.arange(start, dim + start - patch, dim_step), dim + start - patch])
            steps += [starts]
        
        print(box)
        for k, starts in enumerate(steps):
            starts = starts[(starts>box[k]) & (starts<box[k+2])]
            print(starts)
        # my_partial = partial(paint_synapses_in_box,
        #                      self.args['rating_conditions'],
        #                      collection_id,
        #                      rating_source_id,
        #                      self.args['cv_output'],
        #                      chunk_size)
        # pool = Pool(15)

        # #pool.map(my_partial, itertools.product(*steps))
        # for step in itertools.product(*steps):
        #     my_partial(step)
        # #paint_synapses(cv_seg, rating_query.all())


if __name__ == '__main__':
    mod = MaterializeSynapseSparseGroundTruth(input_data=example_parameters)
    mod.run()
