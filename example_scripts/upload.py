import renderapi
from synapsedb.volumes.models import DataSet, Volume, ImageChannel
import argschema
from synapsedb import db


class RenderParameters(argschema.schemas.DefaultSchema):
    host = argschema.fields.String(required=True)
    port = argschema.fields.Int(required=True)
    owner = argschema.fields.String(required=True)
    project = argschema.fields.String(required=True)


class VolUploadParameters(argschema.ArgSchema):
    render = argschema.fields.Nested(RenderParameters, required=True)
    mult_chan_stacks = argschema.fields.List(
        argschema.fields.String, required=True)
    regular_stacks = argschema.fields.List(
        argschema.fields.String, required=True)
    regular_stacks_names = argschema.fields.List(
        argschema.fields.String, required=True)
    volume_name = argschema.fields.String(required=True)


def upload_mult_chan_stacks(volume, mult_chan_stacks, render, db):
    for stack in mult_chan_stacks:
        metadata = renderapi.stack.get_full_stack_metadata(
            stack, render=render)

        channelNames = metadata['stats']['channelNames']
        for channel in channelNames:
            url = "render://{}:{}/{}/{}/{}/{}".format(render.DEFAULT_HOST,
                                                      render.DEFAULT_PORT,
                                                      render.DEFAULT_OWNER,
                                                      render.DEFAULT_PROJECT,
                                                      stack,
                                                      channel)
            color = ''
            default_on = False
            if ('DAPI1' in channel):
                color = 'C'
                default_on = True
            if ('MBP' in channel):
                color = 'M'
                default_on = True
            if ('PSD' in channel):
                color = 'R'
                default_on = True
            if ('raw' in channel):
                default_on = False
            channel = ImageChannel(name=channel,
                                   source_url=url,
                                   volume=volume,
                                   default_channel=default_on,
                                   default_color=color)
            db.session.add(channel)


def upload_render_regular_stack(volume, stack, name, render, db):
    url = "render://{}:{}/{}/{}/{}".format(render.DEFAULT_HOST,
                                           render.DEFAULT_PORT,
                                           render.DEFAULT_OWNER,
                                           render.DEFAULT_PROJECT,
                                           stack)
    channel = ImageChannel(name=name,
                           source_url=url,
                           volume=volume,
                           default_channel=True,
                           default_color=None)
    db.session.add(channel)


def upload_render_regular_stacks(volume, stacks, names, render, db):
    for stack, name in zip(stacks, names):
        upload_render_regular_stack(volume, str(stack), str(name), render, db)


class VolUpload(argschema.ArgSchemaParser):
    default_schema = VolUploadParameters

    def run(self):
        render = renderapi.render.Render(**self.args['render'])
        owner = self.args['render']['owner']
        project = self.args['render']['project']
        vol_name = self.args['volume_name']

        ds = DataSet.query.filter_by(
            render_owner=owner, render_project=project).first()
        volume = Volume(name=vol_name, dataset=ds)
        db.session.add(volume)

        upload_mult_chan_stacks(
            volume, self.args['mult_chan_stacks'], render, db)
        upload_render_regular_stacks(volume,
                                     self.args['regular_stacks'],
                                     self.args['regular_stacks_names'],
                                     render,
                                     db)

        db.session.commit()
