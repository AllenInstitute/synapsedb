# Import flask dependencies
from flask import Blueprint, render_template, redirect, url_for, current_app
# Import the database object from the main app module
from synapsedb.volumes.schemas import DataSetSchema, VolumeSchema
import pandas as pd
# Import module models (i.e. User)
from synapsedb.volumes.models import Volume, DataSet, SourceChannel, ImageChannel
from .forms import ChannelsForm
import ndviz
# Define the blueprint: 'auth', set its url prefix: app.url/auth
mod_volumes = Blueprint('volumes', __name__, url_prefix='/volumes')
pd.set_option('display.max_colwidth', -1)


def named_objects_to_df(objects, schema, url):
    df = pd.DataFrame(data=schema.dump(objects, many=True))
    df['name'] = df.apply(lambda x:
                          "<a href='{}'>{}</a>".format(url_for(url,
                                                               id=x.id),
                                                       x['name']),
                          axis=1)
    return df


@mod_volumes.route("/")
def index():
    datasets = DataSet.query.all()
    df = named_objects_to_df(datasets, DataSetSchema(), '.view_dataset')
    return render_template('table.html', table=df.to_html(escape=False))


@mod_volumes.route("/dataset/<id>")
def view_dataset(id):

    datasets = DataSet.query.filter_by(id=id)
    df = named_objects_to_df(datasets, DataSetSchema(), '.view_dataset')
    df_vol = named_objects_to_df(datasets[0].volumes,
                                 VolumeSchema(),
                                 '.view_volume')
    return render_template('tables.html',
                           tables=[df.to_html(escape=False),
                                   df_vol.to_html(escape=False)],
                           titles=['header', 'volumes'])


color_lookup = {
    "R": 1,
    "G": 2,
    "B": 3,
    "C": 4,
    "M": 5,
    "Y": 6,
    "W": None
}


@mod_volumes.route("/link", methods=["POST"])
def make_link():
    form = ChannelsForm()
    if form.validate_on_submit():
        channels = []
        for form_channel in form.channels:
            if form_channel.include.data:
                id = int(form_channel.channel_id.data)
                channel = SourceChannel.query.filter_by(id=id)[0]
                if isinstance(channel, ImageChannel):
                    channel.default_color = form_channel.color.data
                channels.append(channel)

        state = ndviz.ViewerState()
        for channel in channels:
            layer = ndviz.Layer()
            layer.type = channel.type
            layer._json_data['source'] = channel.source_url
            if channel.type == 'image':
                layer._json_data['blend'] = 'additive'
                layer._json_data['color'] = color_lookup.get(
                    channel.default_color, None)
            state.layers[channel.name] = layer
        url = ndviz.to_url(state, prefix=form.neuroglancer_prefix.data)
        return redirect(url)

    else:
        return "not valid data {}".format(form.data)


@mod_volumes.route("/volume/<id>")
def view_volume(id):
    try:
        volume = Volume.query.filter_by(id=id)[0]
    except IndexError:
        return "no volume found"
    form = ChannelsForm()
    form.neuroglancer_prefix.data = current_app.config['NEUROGLANCER_URL']
    for channel in volume.channels:
        form.channels.append_entry()
    for channel, entry in zip(volume.channels, form.channels.entries):
        entry.label.text = channel.name
        if isinstance(channel, ImageChannel):
            entry.include.data = channel.default_channel
            entry.color.data = channel.default_color
        entry.channel_id.data = channel.id
    return render_template('volume.html',
                           volume=volume,
                           form=form,
                           url=url_for('.make_link'))
