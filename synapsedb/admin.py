from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from synapsedb.volumes.models import Volume, ImageChannel, DataSet, VolumeLink, SegmentationChannel
from synapsedb.synapses.models import SynapseCollection, Synapse
from synapsedb.ratings.models import RatingSource, ClassificationType, Rating


class NoTypeView(ModelView):
    form_excluded_columns = ['type']


def setup_admin(app, db):
    admin = Admin(app, name="synapsedb")
    admin.add_view(ModelView(DataSet, db.session, category='Volumes'))
    admin.add_view(ModelView(Volume, db.session, category='Volumes'))
    admin.add_view(NoTypeView(ImageChannel, db.session, category='Volumes'))
    admin.add_view(NoTypeView(SegmentationChannel,
                              db.session,
                              category='Volumes'))
    admin.add_view(NoTypeView(VolumeLink, db.session, category='Volumes'))
    admin.add_view(NoTypeView(SynapseCollection,
                              db.session, category='Synapses'))
    admin.add_view(NoTypeView(Synapse, db.session, category='Synapses'))
    admin.add_view(ModelView(RatingSource, db.session, category='Ratings'))
    admin.add_view(ModelView(ClassificationType,
                             db.session, category='Ratings'))
    admin.add_view(ModelView(Rating, db.session, category='Ratings' ))
    return admin
