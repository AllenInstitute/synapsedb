# Import flask dependencies
from flask import Blueprint, jsonify
from synapsedb.ratings.models import Rating, RatingSource
import json
from synapsedb import db
mod_ratings = Blueprint('ratings', __name__, url_prefix='/ratings')


@mod_ratings.route("/")
def index():
    return "hello ratings"


@mod_ratings.route("/ratingsource/<ratingsource_id>/")
def get_ratingsource(ratingsource_id):
    return "{}".format(ratingsource_id)


@mod_ratings.route("/ratings_of/<object_id>/ratingsources")
def get_ratingsources_of_object(object_id):
    results = db.session.query(
        Rating.rating_source_id).filter_by(
        object_id=object_id).group_by(
        Rating.rating_source_id).all()
    print(results)
    return jsonify([result[0] for result in results])


@mod_ratings.route("/ratings_of/<object_id>/ratingsource/<ratingsource_id>/")
def get_ratings_of_object_by_source(ratingsource_id, object_id):
    ratings = Rating.query.filter_by(rating_source_id=ratingsource_id,
                                     object_id=object_id)
    d = {}
    for rating in ratings:
        d[rating.classificationtype.name] = rating.get_rating()

    return jsonify(d)
