# Import flask dependencies
from flask import Blueprint, render_template, url_for, request, redirect
import pandas as pd
from synapsedb import db
# Import module models (i.e. User)
from .models import Synapse, SynapseCollection
from .schemas import SynapseCollectionSchema
from synapsedb.ratings.controllers import get_rating_summary_df
# from geoalchemy2 import Geometry
# from geoalchemy2.shape import from_shape, to_shape
from synapsedb.volumes.models import VolumeLink
from synapsedb.synapses.postgis import Box3D, ST_XMin, ST_YMin, ST_ZMin, ST_XMax, ST_YMax, ST_ZMax
from synapsedb.synapses.schemas import SynapseSchema
from synapsedb.synapses.forms import SynapseViewForm
from functools import partial
import numpy as np
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


@mod_synapses.route("/synapsecollections")
def get_synapsecollections():
    collection = SynapseCollection.query.all()
    schema = SynapseCollectionSchema(exclude=['objects'])
    return schema.jsonify(collection, many=True)


@mod_synapses.route("/view/synapsecollection/<id>/oid/<oid>")
def view_synapse_by_collection_oid(id, oid):
    synapse = Synapse.query.filter_by(object_collection_id=id, oid=oid).first()
    return view_synapse(synapse.id)


@mod_synapses.route("/synapsecollection/<id>")
def get_synapsecollection(id):
    collection = SynapseCollection.query.filter_by(id=id).first()
    schema = SynapseCollectionSchema()
    return schema.jsonify(collection)


@mod_synapses.route("/view/synapsecollection/<id>", methods=["GET", "POST"])
def view_synapsecollection(id):
    form = SynapseViewForm()
    if request.method == 'POST':
        print(form.object_id.data)
        print(form.oid.data)
        if form.object_id.data is not None:
            return redirect(url_for('.view_synapse',
                                    id=form.object_id.data))
        if form.oid.data is not None:
            return redirect(url_for('.view_synapse_by_collection_oid',
                                    id=id,
                                    oid=form.oid.data))
    collection = SynapseCollection.query.filter_by(id=id).first_or_404()
    query = Synapse.query.with_entities(Synapse.id,
                                        Synapse.oid,
                                        (ST_XMin(Synapse.areas) +
                                         ST_XMax(Synapse.areas)) / 2,
                                        (ST_YMin(Synapse.areas) +
                                         ST_YMax(Synapse.areas)) / 2,
                                        (ST_ZMin(Synapse.areas) +
                                         ST_ZMax(Synapse.areas)) / 2)\
        .filter(Synapse.object_collection_id == id)
    df = pd.read_sql(query.statement, db.session.bind)
    for k, row in df.iterrows():
        url = make_synapse_link_fast(
            collection.link, [row.anon_1, row.anon_2, row.anon_3])
        if url is not None:
            df.loc[k, 'link'] = "<a href='{}'>vizlink</a>".format(url)
        else:
            df.loc[k, 'link'] = ""

    df['id'] = df.id.map(lambda x: "<a href='{}'>{}</a>"
                         .format(url_for('.view_synapse', id=x), x))
    df_cut = df[['id', 'oid', 'link']]

    form.collection_id.data = collection.id
    return render_template('synapse_collection.html',
                           collection=collection,
                           table=df_cut.to_html(index=False,
                                                escape=False,
                                                max_rows=2000),
                           form=form)


def get_box_as_array(box3d):
    minX = db.session.scalar(box3d.ST_XMin())
    minY = db.session.scalar(box3d.ST_YMin())
    minZ = db.session.scalar(box3d.ST_ZMin())
    maxX = db.session.scalar(box3d.ST_XMax())
    maxY = db.session.scalar(box3d.ST_YMax())
    maxZ = db.session.scalar(box3d.ST_ZMax())
    return (minX, minY, minZ, maxX, maxY, maxZ)


def get_box_center(box3d):
    (minX, minY, minZ, maxX, maxY, maxZ) = get_box_as_array(box3d)
    return [(maxX + minX) / 2, (maxY + minY) / 2, (maxZ + minZ) / 2]


@mod_synapses.route("/synapse/<id>")
def view_synapse_json(id):
    synapse = Synapse.query.filter_by(id=id).first()
    schema = SynapseSchema()
    return schema.jsonify(synapse)


def make_synapse_link_fast(link, center_box):
    if link is not None:
        urlp = parse.urlparse(link.link)
        state = ndviz.parse_url(link.link)
        state.voxel_coordinates = center_box
        nglancprefix = "{}://{}".format(urlp.scheme, urlp.netloc)
        url = ndviz.to_url(state, prefix=nglancprefix)
        return url
    else:
        return None


def make_synapse_link(synapse, center_box=None):
    link = synapse.collection.link
    if (center_box is None):
        box3d = Box3D(synapse.areas)
        center_box = get_box_center(box3d)
    url = make_synapse_link_fast(link, center_box)
    return url


@mod_synapses.route("/view/synapse/<id>")
def view_synapse(id):
    synapse = Synapse.query.filter_by(id=id)[0]
    # shape = to_shape(synapse.areas)
    # print(type(synapse.areas.ST_GeometricMedian()))

    box3d = Box3D(synapse.areas)
    center_box = get_box_center(box3d)

    rating_df = get_rating_summary_df(synapse.id)
    if rating_df is not None:
        rating_html = rating_df.to_html(escape=False)
    else:
        rating_html = None
    url = make_synapse_link_fast(synapse.collection.link, center_box)
    # print(to_shape(centroid))
    return render_template("synapse.html",
                           center=center_box,
                           synapse=synapse,
                           link_url=url,
                           rating_table=rating_html)
