# Import flask dependencies
from flask import Blueprint

mod_ratings = Blueprint('ratings', __name__, url_prefix='/ratings')


@mod_ratings.route("/")
def index():
    return "hello ratings"
