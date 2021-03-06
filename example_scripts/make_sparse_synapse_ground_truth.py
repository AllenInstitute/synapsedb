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
import tifffile

example_parameters = {
    "scale": "0.03125",
    "output_label_file": "/nas5/label_test.tiff",
    "output_mask_file": "/nas5/mask_test.tiff",
    "synapse_collection_id": 2,
    "rating_source_id": 24,
    "cv_for_bounds": "file:///nas3/data/M247514_Rorb_1/processed/Site3Align2Stacks/cv_Site3Align2_EM_clahe_mm",
    "cv_outputs": "file:///nas3/data/M247514_Rorb_1/processed/Site3Align2Stacks/cv_synapses",
    "rating_conditions": [{
        "classification_type": "GABA",
        "rating": False
    },
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
    scale = argschema.fields.Float(required=True, description="synapse float")
    cv_for_bounds = argschema.fields.String(required=True, description="path to cloud volume to use for base metadata")
    cv_output = argschema.fields.String(required=True, description="path to cloud volume to save annotations into")
    output_label_file = argschema.fields.OutputFile(
        required=True, description="path to save label file")
    output_mask_file =  argschema.fields.OutputFile(
        required=True, description="path to save mask file")
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


def paint_synapse_masks(label, mask, synapses, mins, scale, in_class=True):
    for synapse, count in synapses:
        multPolygon = shape.to_shape(synapse.areas)
        for poly in multPolygon.geoms:
            exterior = poly.exterior
            z = int(exterior.coords[0][2])
            label_patch = np.zeros(label.shape[1:], dtype=np.uint8)
            mask_patch = np.zeros(label.shape[1:], dtype=np.uint8)
            path = scale * (exterior.xy - mins[0:2, np.newaxis])
            if in_class:
                label_patch = cv2.fillPoly(
                    label_patch, [np.int64(path.T)], 1)
            mask_patch = cv2.fillPoly(
                mask_patch, [np.int64(path.T)], 1)

            for interior in poly.interiors:
                path = scale * (interior.xy - mins[0:2, np.newaxis])
                if in_class:
                    label_patch = cv2.fillPoly(
                        label_patch, [np.int64(path.T)], not in_class)
                mask_patch = cv2.fillPoly(
                    mask_patch, [np.int64(path.T)], 0)
            mask[z, :, :] += mask_patch
            if in_class:
                label[z, :, :] += label_patch
            
    return label, mask


class MaterializeSynapseSparseGroundTruth(argschema.ArgSchemaParser):
    default_schema = MaterializeSynapseSparseGroundTruthParameters

    def run(self):
        collection_id = self.args['synapse_collection_id']
        rating_source_id = self.args['rating_source_id']

        filters = []
        inverse_filters = []
        for rating_condition in self.args['rating_conditions']:
            filter, inverse_filter = construct_filters(rating_condition)
            filters.append(filter)
            inverse_filters.append(inverse_filter)

        rating_query = get_has_all_rating_query(
            collection_id, rating_source_id, filters)
        rating_false_query = get_has_any_rating_query(
            collection_id, rating_source_id, inverse_filters)

        box = Synapse.query.with_entities(ST_3DExtent(Synapse.areas))\
            .filter_by(object_collection_id=collection_id).first()[0]

        print(rating_query.count())
        print(rating_false_query.count())
        print(rating_query.first())
        print(get_box_as_array(box))

        #bounds = np.array(get_box_as_array(box))
        #mins = bounds[0:3]
        #maxs = bounds[3:]
        scale = self.args['scale']
        sizes = np.uint16(scale * (maxs - mins))
        sizes[2] = maxs[2] - mins[2] + 1
        sizes = np.flip(sizes, 0)
        label = np.zeros(sizes, dtype=np.uint8)
        mask = np.zeros(sizes, dtype=np.uint8)

        label, mask = paint_synapse_masks(label, mask,
                                          rating_false_query.all(),
                                          mins,
                                          scale,
                                          in_class=False)

        label, mask = paint_synapse_masks(label, mask,
                                          rating_query.all(),
                                          mins,
                                          scale,
                                          in_class=True)


        tifffile.imsave(self.args['output_label_file'], label)
        tifffile.imsave(self.args['output_mask_file'], mask)


if __name__ == '__main__':
    mod = MaterializeSynapseSparseGroundTruth(input_data=example_parameters)
    mod.run()
