from synapsedb import db
from geoalchemy2 import Geometry
from synapsedb.volumes.models import Volume
from .config import SYNAPSE_SRID


class NamedModel(object):
    name = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return "{}({})".format(self.name, self.id)


class BioObjectCollection(NamedModel, db.Model):
    __tablename__ = 'bioobjectcollection'
    volume_id = db.Column(db.Integer, db.ForeignKey('volume.id'))
    volume = db.relationship('Volume')
    type = db.Column(db.String(32))
    __mapper_args__ = {
        'polymorphic_on': 'type',
        'polymorphic_identity': 'employee'
    }


class SynapseCollection(BioObjectCollection):
    __tablename__ = None  # Add table name to be None
    __mapper_args__ = {
        'polymorphic_identity': 'synapsecollection'
    }
    synapse_collection_type = db.Column(db.String(100))


class BioObject(db.Model):
    __tablename__ = "bioobject"  # Add table name to be None
    __mapper_args__ = {
        'polymorphic_identity': 'bioobject',
        'polymorphic_on': 'type',
    }
    object_collection_id = db.Column(db.Integer,
                                     db.ForeignKey('bioobjectcollection.id'))
    collection = db.relationship(BioObjectCollection)
    type = db.Column(db.String(32))


class Synapse(BioObject):
    __tablename__ = None  # Add table name to be None
    __mapper_args__ = {
        'polymorphic_identity': 'synapse'
    }
    oid = db.Column(db.String(50))
    areas = db.Column(Geometry(geometry_type="MULTIPOLYGONZ",
                               management=True,
                               use_typmod=False,
                               srid=SYNAPSE_SRID,
                               dimension=3))


# class IntegerRating(Rating):
#     __tablename__ = None
#     __mapper_args__ = {
#         'polymorphic_identity': 'tertiary',
#     }

# class HumanRater(NamedModel):
#     pass


# class UserRatingSource(ClassSource):
#     human_rater_id = db.Column(db.Integer, db.ForeignKey('HumanRater.id'))
