from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from synapsedb.volumes.models import Volume, ImageChannel, DataSet, VolumeLink
from synapsedb.synapses.models import SynapseCollection, Synapse


class NoTypeView(ModelView):
    form_excluded_columns = ['type']


def setup_admin(app, db):
    admin = Admin(app, name="synapsedb")
    admin.add_view(ModelView(DataSet, db.session))
    admin.add_view(ModelView(Volume, db.session))
    admin.add_view(NoTypeView(ImageChannel, db.session))
    admin.add_view(NoTypeView(VolumeLink, db.session))
    admin.add_view(NoTypeView(SynapseCollection, db.session))
    admin.add_view(NoTypeView(Synapse, db.session))
    return admin
