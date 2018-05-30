from synapsedb import db
from synapsedb.synapses.models import BioObject
from sqlalchemy.dialects.postgresql import ARRAY
from datetime import datetime


class NamedModel(object):
    name = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return "{}({})".format(self.name, self.id)


class RatingSource(NamedModel, db.Model):
    __tablename__ = "ratingsource"
    type = db.Column(db.String(32))
    __mapper_args__ = {
        'polymorphic_identity': 'ratingsource',
        'polymorphic_on': 'type',
    }


class ConsensusSource(RatingSource):
    rating_sources = db.Column(ARRAY(db.Integer))
    __tablename__ = None
    __mapper_args__ = {
        'polymorphic_identity': 'consensus',
    }


class MachineLearningSource(RatingSource):
    algorithm = db.Column(db.String(100))
    __tablename__ = None
    __mapper_args__ = {
        'polymorphic_identity': 'machinelearning',
    }


class UserRatingSource(RatingSource):
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    __tablename__ = None
    __mapper_args__ = {
        'polymorphic_identity': 'user',
    }


class User(db.Model):
    __bind_key__ = 'users'
    __tablename__ = 'users'
    user_name = db.Column(db.String(255))
    created = db.Column(db.DateTime, nullable=False, default=datetime.now())


class ClassificationType(NamedModel, db.Model):
    __tablename__ = "classificationtype"
    rating_type = db.Column(db.String(40))


class TimestampMixin(object):
    created = db.Column(
        db.DateTime, nullable=False, default=datetime.now())
    updated = db.Column(db.DateTime, onupdate=datetime.now())


class Rating(TimestampMixin, db.Model):
    __tablename__ = "rating"
    type = db.Column(db.String(32))
    object_id = db.Column(db.Integer, db.ForeignKey('bioobject.id'))
    rating_source_id = db.Column(db.Integer, db.ForeignKey('ratingsource.id'))
    classificationtype_id = db.Column(
        db.Integer, db.ForeignKey('classificationtype.id'))
    confidence = db.Column(db.Float)
    classificationtype = db.relationship('ClassificationType')
    rating_source = db.relationship('RatingSource')

    def get_rating(self):
        '''generic function, need to implement for class'''
        pass

    __mapper_args__ = {
        'polymorphic_identity': 'rating',
        'polymorphic_on': 'type',
    }


class BinaryRating(Rating):
    __tablename__ = None
    __mapper_args__ = {
        'polymorphic_identity': 'binary',
    }
    bool_rating = db.Column(db.Boolean)

    def get_rating(self):
        return self.bool_rating


class TertiaryRating(Rating):
    __tablename__ = None
    __mapper_args__ = {
        'polymorphic_identity': 'tertiary',
    }
    tert_rating = db.Column(db.Integer)

    def get_rating(self):
        return self.tert_rating
