import argschema
from shapely import geometry
import geoalchemy2
from sqlalchemy.sql.expression import or_, any_
from sqlalchemy import func
from synapsedb import db
from synapsedb.synapses.models import Synapse
from synapsedb.ratings.models import Rating, ClassificationType

example_parameters = {
    "synapse_collection_id":2,
    "rating_source_id":24,
    "rating_conditions":[{
                            "classification_type":"GABA",
                            "rating":False
                         },
                         {
                            "classification_type":"Synapse",
                            "rating":True
                        }]
    }


class RatingRequirements(argschema.schemas.DefaultSchema):
    classification_type = argschema.fields.String(required=True, description="name of classification type")
    rating = argschema.fields.Raw(required=True, description="rating that should be returned")

class MaterializeSynapseSparseGroundTruthParameters(argschema.ArgSchema):
    synapse_collection_id = argschema.fields.Integer(required=True, description="id of synapse collection")
    rating_source_id = argschema.fields.Integer(required=True, description="id of rating source to use")
    rating_conditions = argschema.fields.Nested(RatingRequirements,
                                               many=True,
                                               description="what ratings this synapse must have to be included")


def get_all_relevant_ratings_query(collection_id,rating_source_id,filters):
    # get all the synapses in this collection
    synapse_query = Synapse.query.filter_by(object_collection_id=collection_id)
    # filter the Ratings on those synapses that meet one of the filters
    # then grouped by synapse, so you can count how many conditions each passed
    rating_query = synapse_query.join(Rating, Rating.object_id==Synapse.id)\
            .with_entities(Rating.object_id, func.count(Rating.object_id))\
            .filter(Rating.rating_source_id==rating_source_id)\
            .filter(or_(*filters))\
            .group_by(Rating.object_id)
    return rating_query

def get_has_any_rating_query(collection_id, rating_source_id, filters):
    # a grouped query for all the relevant ratings that passed one of the filters
    base_query = get_all_relevant_ratings_query(collection_id, rating_source_id, filters)
    # return those that have any of the relevant ratings
    return base_query.having(func.count(Rating.object_id)>0)

def get_has_all_rating_query(collection_id, rating_source_id, filters):
    # a grouped query for all the relevant ratings that passed one of the filters
    base_query = get_all_relevant_ratings_query(collection_id, rating_source_id, filters)
    # return those that have any all the relevant ratings
    return base_query.having(func.count(Rating.object_id)==len(filters))

def construct_filters(rating_condition):
    type_lookup ={
        "BinaryRating":"bool_rating",
        "TertiaryRating":"tert_rating"
    }
    #get the classification type for this rating condition
    class_type = ClassificationType.query.filter_by(
                name=rating_condition['classification_type']).first()
    assert(class_type is not None)

    #get the column where the rating is stored
    rating_col = getattr(Rating,type_lookup[class_type.rating_type])

    #construct the condition that this rating is what it should be
    filter = (rating_col==rating_condition['rating'])&\
                (Rating.classificationtype==class_type)

    #and that this rating is not what it should be
    inverse_filter = (rating_col!=rating_condition['rating'])&\
                (Rating.classificationtype==class_type)
    return (filter,inverse_filter)

class MaterializeSynapseSparseGroundTruth(argschema.ArgSchemaParser):
    default_schema= MaterializeSynapseSparseGroundTruthParameters

    def run(self):
        collection_id = self.args['synapse_collection_id']
        rating_source_id = self.args['rating_source_id']

        filters =[]
        inverse_filters = []
        for rating_condition in self.args['rating_conditions']:   
            filter, inverse_filter = construct_filters(rating_condition)
            filters.append(filter)
            inverse_filters.append(inverse_filter)

        rating_query = get_has_all_rating_query(collection_id,rating_source_id,filters)
        rating_false_query = get_has_any_rating_query(collection_id,rating_source_id,inverse_filters)

        print(rating_query.count())
        print(rating_false_query.count())



if __name__ == '__main__':
    mod = MaterializeSynapseSparseGroundTruth(input_data=example_parameters)
    mod.run()


