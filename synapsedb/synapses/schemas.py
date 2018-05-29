from synapsedb import ma
from .models import Synapse, SynapseCollection
from marshmallow_sqlalchemy import ModelConverter
from geoalchemy2 import Geometry
from marshmallow import fields


class GeoConverter(ModelConverter):
    SQLA_TYPE_MAPPING = ModelConverter.SQLA_TYPE_MAPPING.copy()
    SQLA_TYPE_MAPPING.update({
        Geometry: fields.Str
    })


class SynapseCollectionSchema(ma.ModelSchema):
    class Meta:
        model = SynapseCollection


class SynapseSchema(ma.ModelSchema):
    class Meta:
        model = Synapse
        model_converter = GeoConverter


