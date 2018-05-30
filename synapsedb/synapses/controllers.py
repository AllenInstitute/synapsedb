# Import flask dependencies
from flask import Blueprint, render_template, url_for
import pandas as pd
from synapsedb import db
# Import module models (i.e. User)
from .models import Synapse, SynapseCollection
from .schemas import SynapseCollectionSchema
from synapsedb.ratings.controllers import get_rating_summary_df
# from geoalchemy2 import Geometry
# from geoalchemy2.shape import from_shape, to_shape
from synapsedb.volumes.models import VolumeLink
from synapsedb.synapses.postgis import Box3D
import ndviz
try:
    from urllib import parse
except ImportError:
    import urlparse as parse
# import ndviz
# Define the blueprint: 'auth', set its url prefix: app.url/auth
mod_synapses = Blueprint('synapses', __name__, url_prefix='/synapses')
pd.set_option('display.max_colwidth', -1)


def named_objects_to_df(objects, schema, url):
    df = pd.DataFrame(data=schema.dump(objects, many=True))
    df['name'] = df.apply(lambda x:
                          "<a href='{}'>{}</a>".format(url_for(url,
                                                               id=x.id),
                                                       x['name']),
                          axis=1)
    return df


@mod_synapses.route("/")
def index():
    collections = SynapseCollection.query.all()
    df = named_objects_to_df(collections,
                             SynapseCollectionSchema(),
                             '.view_synapsecollection')
    return render_template('table.html', table=df.to_html(escape=False))


@mod_synapses.route("/synapsecollection/<id>")
def view_synapsecollection(id):
    collections = SynapseCollection.query.filter_by(id=id)
    df = named_objects_to_df(collections,
                             SynapseCollectionSchema(),
                             '.view_synapsecollection')
    return render_template('table.html', table=df.to_html(escape=False))


def get_box_center(box3d):
    minX = db.session.scalar(box3d.ST_XMin())
    minY = db.session.scalar(box3d.ST_YMin())
    minZ = db.session.scalar(box3d.ST_ZMin())
    maxX = db.session.scalar(box3d.ST_XMax())
    maxY = db.session.scalar(box3d.ST_YMax())
    maxZ = db.session.scalar(box3d.ST_ZMax())
    return [(maxX + minX) / 2, (maxY + minY) / 2, (maxZ + minZ) / 2]


@mod_synapses.route("/synapse/<id>")
def view_synapse(id):
    synapse = Synapse.query.filter_by(id=id)[0]
    # shape = to_shape(synapse.areas)
    # print(type(synapse.areas.ST_GeometricMedian()))
    box3d = Box3D(synapse.areas)
    center_box = get_box_center(box3d)
    vid = synapse.collection.volume_id
    link = VolumeLink.query.filter_by(name='SynapseView',
                                      volume_id=vid).first()

    rating_df = get_rating_summary_df(synapse.id)

    if link is not None:
        urlp = parse.urlparse(link.link)
        state = ndviz.parse_url(link.link)
        state.voxel_coordinates = center_box
        nglancprefix = "{}://{}".format(urlp.scheme, urlp.netloc)
        url = ndviz.to_url(state, prefix=nglancprefix)
    else:
        url = None
    # print(to_shape(centroid))
    return render_template("synapse.html",
                           center=center_box,
                           synapse=synapse,
                           link_url=url,
                           rating_table=rating_df.to_html(escape=False))
