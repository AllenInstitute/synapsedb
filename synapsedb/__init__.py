from flask import Flask  # , render_template
from flask_sqlalchemy import SQLAlchemy, Model
from flask_migrate import Migrate
from flask_marshmallow import Marshmallow
from sqlalchemy.ext.declarative import declared_attr
import sqlalchemy as sa
from synapsedb.config import configure_app
from synapsedb.utils import get_instance_folder_path


# Import a module / component using its blueprint handler variable (mod_auth)


# Define the WSGI application object
app = Flask(__name__,
            instance_path=get_instance_folder_path(),
            instance_relative_config=True)
configure_app(app)


class IdModel(Model):
    @declared_attr
    def id(cls):
        for base in cls.__mro__[1:-1]:
            if getattr(base, '__table__', None) is not None:
                type = sa.ForeignKey(base.id)
                break
        else:
            type = sa.Integer

        return sa.Column(type, primary_key=True)


# Define the database object which is imported
# by modules and controllers
db = SQLAlchemy(app, model_class=IdModel)

ma = Marshmallow(app)
migrate = Migrate(app, db)

from synapsedb.admin import setup_admin  # noQA: E402
admin = setup_admin(app, db)

# Sample HTTP error handling
# @app.errorhandler(404)
# def not_found(error):
#     return render_template('404.html'), 404

from synapsedb.volumes.controllers import mod_volumes as volumes_module  # noQA: E402,E501
from synapsedb.synapses.controllers import mod_synapses as synapses_module  # noQA: E402,E501
from synapsedb.ratings.controllers import mod_ratings as ratings_module  # noQA: E402,E501
# Register blueprint(s)
app.register_blueprint(volumes_module)
app.register_blueprint(synapses_module)
app.register_blueprint(ratings_module)


# Build the database:
# This will create the database file using SQLAlchemy
db.create_all()

# from flask import Flask
# if __name__ == '__main__':
#     db.init_app(app)
#     app.run(debug=True, port=6000)

# import synapsedb.models
# import synapsedb.admin  # noQA: E402
# import synapsedb.views  # noQA: F401, E402


@app.route("/")
def index():
    return "hello world"
