import renderapi
from synapsedb import db
from synapsedb.volumes.models import DataSet, Volume, ImageChannel

owner = "Forrest"
project = "M247514_Rorb_1"
script_loc = "/Users/forrestc/RenderStack/render/render-ws-java-client/src/main/scripts/"  # noQA: E501
render_params = {
    "host": "ibs-forrestc-ux1.corp.alleninstitute.org",
    "port": "80",
    "owner": owner,
    "project": project,
    "client_scripts": script_loc
}

render = renderapi.connect(**render_params)
channels = ImageChannel.query.all()
volumes = Volume.query.all()
datasets = DataSet.query.all()
for obj in channels + volumes + datasets:
    db.session.delete(obj)


ds = DataSet(name=project, render_owner=owner, render_project=project)
db.session.add(ds)

volume = Volume(name="BIG ALIGN LENS", dataset=ds)
db.session.add(volume)


mult_chan_stacks = ["BIGALIGN_LENS_Session1",
                    "BIGALIGN_LENS_Session2",
                    "BIGALIGN_LENS_Session3"]
for stack in mult_chan_stacks:
    metadata = renderapi.stack.get_full_stack_metadata(stack, render=render)

    channelNames = metadata['stats']['channelNames']
    for channel in channelNames:
        url = renderapi.render.format_preamble(render.DEFAULT_HOST,
                                               render.DEFAULT_PORT,
                                               owner,
                                               project,
                                               stack)
        url = "render://{}:{}/{}/{}/{}/{}".format(render.DEFAULT_HOST,
                                                  render.DEFAULT_PORT,
                                                  owner,
                                                  project,
                                                  stack,
                                                  channel)
        color = ''
        default_on = False
        if 'DAPI1' in channel:
            color = 'C'
            default_on = True
        if 'MBP' in channel:
            color = 'M'
            default_on = True
        if 'EM' in channel:
            color = ''
            default_on = True
        if 'PSD' in channel:
            color = 'R'
            default_on = True
        channel = ImageChannel(name=channel,
                               source_url=url,
                               volume=volume,
                               default_channel=default_on,
                               default_color=color)
        db.session.add(channel)

em_stack = "BIGALIGN_LENS_EMclahe_all"

url = "render://{}:{}/{}/{}/{}".format(render.DEFAULT_HOST,
                                       render.DEFAULT_PORT,
                                       owner,
                                       project,
                                       em_stack)
em_channel = ImageChannel(name="EM", source_url=url, volume=volume)
db.session.add(em_channel)
db.session.commit()
