from synapsedb import ma
import synapsedb.volumes.models as models


class DataSetSchema(ma.ModelSchema):
    class Meta:
        model = models.DataSet


class VolumeSchema(ma.ModelSchema):
    class Meta:
        model = models.Volume


class SourceChannelSchema(ma.ModelSchema):
    class Meta:
        model = models.SourceChannel
