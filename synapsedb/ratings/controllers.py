# Import flask dependencies
from flask import Blueprint, jsonify
from synapsedb.ratings.models import Rating, RatingSource
import json
mod_ratings = Blueprint('ratings', __name__, url_prefix='/ratings')


@mod_ratings.route("/")
def index():
    return "hello ratings"

@mod_ratings.route("/ratingsource/<ratingsource_id>/")
def get_ratingsource(ratingsource_id):
    return "{}".format(ratingsource_id)


@mod_ratings.route("/ratingsource/<ratingsource_id>/ratings/<object_id>/")
def get_ratings_of(ratingsource_id, object_id):
    ratings = Rating.query.filter_by(rating_source_id=ratingsource_id,
                                     object_id=object_id)
    d = {}
    for rating in ratings:
        d[rating.classificationtype.name] = rating.get_rating()
        
    return jsonify(d)
