# Import flask dependencies
from flask import Blueprint, jsonify
from synapsedb.ratings.models import Rating, ClassificationType, RatingSource
from synapsedb.ratings.schemas import RatingSourceSchema
from synapsedb import db
import pandas as pd
mod_ratings = Blueprint('ratings', __name__, url_prefix='/ratings')

@mod_ratings.route("/ratingsources")
@mod_ratings.route("/")
def index():
    rating_sources = RatingSource.query.all()
    schema = RatingSourceSchema()
    return schema.jsonify(rating_sources, many=True)


@mod_ratings.route("/ratings_of/<object_id>/ratingsource/<ratingsource_id>/rating/<class_name>")
def get_rating(object_id, ratingsource_id, class_name):
    classtype = ClassificationType.query.filter_by(name=class_name).first()
    rating = Rating.query.filter_by(object_id=object_id,
                                    rating_source_id=ratingsource_id,
                                    classificationtype=classtype).first()
    return jsonify(rating.get_rating())


@mod_ratings.route("/ratingsource/<ratingsource_id>")
def get_ratingsource(ratingsource_id):
    rating_source = RatingSource.query.filter_by(id=ratingsource_id).first()
    schema = RatingSourceSchema()
    return schema.jsonify(rating_source)



def get_rating_summary_df(object_id):
    rating_source_ids = get_ratingsources_of_object(object_id).json
    ds = []
    for rating_source_id in rating_source_ids:
        d = get_ratings_of_object_by_source(rating_source_id, object_id).json
        d['rating_source_id'] = rating_source_id
        ds.append(d)
    rating_df = pd.DataFrame(ds)
    rating_df = rating_df.set_index('rating_source_id')
    return rating_df


@mod_ratings.route("/ratings_of/<object_id>")
def get_rating_summary_json(object_id):
    df = get_rating_summary_df(object_id)
    return jsonify(df.to_dict())


@mod_ratings.route("/ratings_of/<object_id>/ratingsources")
def get_ratingsources_of_object(object_id):
    results = db.session.query(
        Rating.rating_source_id).filter_by(
        object_id=object_id).group_by(
        Rating.rating_source_id).all()
    print(results)
    return jsonify([result[0] for result in results])


@mod_ratings.route("/ratings_of/<object_id>/ratingsource/<ratingsource_id>")
def get_ratings_of_object_by_source(ratingsource_id, object_id):
    ratings = Rating.query.filter_by(rating_source_id=ratingsource_id,
                                     object_id=object_id)
    d = {}
    for rating in ratings:
        d[rating.classificationtype.name] = rating.get_rating()

    return jsonify(d)
