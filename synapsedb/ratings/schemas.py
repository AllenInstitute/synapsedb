from synapsedb import ma
import synapsedb.ratings.models as models

class RatingSourceSchema(ma.ModelSchema):
    class Meta:
        model = models.RatingSource


class RatingSchema(ma.ModelSchema):
    class Meta:
        model = models.Rating

