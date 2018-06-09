from flask_wtf import FlaskForm
from wtforms import StringField, HiddenField, IntegerField, validators


class SynapseViewForm(FlaskForm):
    collection_id = HiddenField('object_collection_id')
    object_id = IntegerField('id', validators=[validators.optional()])
    oid = StringField('oid')
