from synapsedb import db
from synapsedb.volumes.models import Volume, DataSet
from synapsedb.synapses.models import Synapse, SynapseCollection
from synapsedb.ratings.models import RatingSource, Rating

ratings_name = "Site3ConsensusRatings"
rating_source = RatingSource.query.filter_by(name=ratings_name).first()

ratings = Rating.query.filter_by(rating_source_id=rating_source.id).all()

for rating in ratings:
    db.session.delete(rating)
db.session.delete(rating_source)
db.session.commit()
