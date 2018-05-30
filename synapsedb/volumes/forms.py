from flask_wtf import FlaskForm
from wtforms import FieldList, BooleanField, RadioField, FormField
from wtforms import StringField, HiddenField


class ChannelForm(FlaskForm):
    channel_id = HiddenField('id')
    include = BooleanField('include', default=False)
    color = RadioField('color', choices=[('G', 'G'),
                                         ('R', 'R'),
                                         ('B', 'B'),
                                         ('Y', 'Y'),
                                         ('M', 'M'),
                                         ('C', 'C'),
                                         ("", "W")], default="")


class ChannelsForm(FlaskForm):
    channels = FieldList(FormField(ChannelForm))
    neuroglancer_prefix = StringField(label="neuroglancer site")
