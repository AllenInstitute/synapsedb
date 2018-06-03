from synapsedb import db


class NamedModel(object):
    name = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return "{}({})".format(self.name, self.id)


class DataSet(NamedModel, db.Model):
    render_project = db.Column(db.String(50))
    render_owner = db.Column(db.String(50))
    volumes = db.relationship('Volume', backref='data_set')


class Volume(NamedModel, db.Model):
    channels = db.relationship('SourceChannel', backref='volume')
    dataset_id = db.Column(db.Integer, db.ForeignKey('data_set.id'))
    dataset = db.relationship('DataSet')
    links = db.relationship('VolumeLink', backref='volume')
    synapse_collections = db.relationship('SynapseCollection',
                                          backref='synvolume')

    def get_neuroglancer_layers(self):
        ds = []
        for chan in self.channels:
            if chan.default_channel:
                d = {
                    'source': chan.source_url,
                    'blend': 'additive'
                }
                if chan.default_color:
                    d['color'] = chan.default_color
                ds.append(d)
        return ds


class SourceChannel(NamedModel, db.Model):
    __tablename__ = 'sourcechannel'
    volume_id = db.Column(db.Integer, db.ForeignKey('volume.id'))
    source_url = db.Column(db.String(250), nullable=False)
    default_channel = db.Column(db.Boolean, nullable=False, default=False)
    type = db.Column(db.String(32), default='image')
    __mapper_args__ = {
        'polymorphic_on': 'type',
        'polymorphic_identity': ''
    }


class ImageChannel(SourceChannel):
    __tablename__ = None
    default_color = db.Column(db.String(1))
    __mapper_args__ = {
        'polymorphic_identity': 'image'
    }


class SegmentationChannel(SourceChannel):
    __tablename__ = None
    __mapper_args__ = {
        'polymorphic_identity': 'segmentation'
    }


class Link(NamedModel, db.Model):
    __tablename__ = 'link'
    type = db.Column(db.String(32))
    link = db.Column(db.String(10000))
    __mapper_args__ = {
        'polymorphic_on': 'type',
        'polymorphic_identity': 'link'
    }

    def get_link_html(self):
        return '<a href="{}">{}</a>'.format(self.link, self.name)


class VolumeLink(Link):
    __tablename__ = None
    volume_id = db.Column(db.Integer, db.ForeignKey('volume.id'))
    __mapper_args__ = {
        'polymorphic_identity': 'volumelink'
    }
