from synapsedb import db
from synapsedb.volumes.models import DataSet, Volume
from synapsedb.ratings.models import ClassificationType, BinaryRating
from synapsedb.ratings.models import ConsensusSource
from synapsedb.synapses.models import Synapse, SynapseCollection
import pandas as pd
import numpy as np
import argschema
import numpy as np

example_parameters = {
    "metadata_csv": "https://docs.google.com/spreadsheets/d/1zp3mApWRo5xyg1tqOSt7Ddp0LC7xWIFaFbsxZrk73bQ/export?gid=0&format=csv",
    "dataset": "M247514_Rorb_1",
    "volume": "Take2Site4",
    "rating_source_name": "Site4ConsensusRatings",
    "synapse_collection": "EM Synapses"
}

example_parameters = {
    "metadata_csv": "https://docs.google.com/spreadsheets/d/1Ecp3kMilsyULcgNde13jBbsQi0Shf6VbBPOk3PQ3qFA/export?gid=0&format=csv",
    "dataset": "M247514_Rorb_1",
    "volume": "Take2Site5",
    "rating_source_name": "Site5ConsensusRatings",
    "synapse_collection": "EM Synapses"
}


example_parameters = {
    "metadata_csv": "https://docs.google.com/spreadsheets/d/1cV6BuQosLgjZX1e2l9EZHTOSLZGlDETKjlv2-wjpeIk/export?gid=607779864&format=csv",
    "dataset": "M247514_Rorb_1",
    "volume": "Site3",
    "rating_source_name": "Site3ConsensusRatings",
    "synapse_collection": "EM Synapses"
}


class InsertRatingsParameters(argschema.ArgSchema):
    metadata_csv = argschema.fields.String(
        required=True, description="path to metadata file")
    dataset = argschema.fields.String(
        required=True, description="name of dataset")
    volume = argschema.fields.String(
        required=True, description="name of volume in dataset")
    rating_source_name = argschema.fields.String(
        required=True, description="name of new rating source")
    synapse_collection = argschema.fields.String(
        required=True, default="EM Syanpses",
        description="name of syanpse collection")


def insert_synapse_row(row, db, syncoll, consensus_source,
                       gaba_type, synapse_type, shaft_type,
                       preRorb_type, postRorb_type):

    synapse = Synapse.query.filter_by(
        collection=syncoll, oid=row.oid).first()
    if synapse is None:
        print("synapse oid {} not found".format(row.oid))
    else:

        isGaba = (row.GABA == 1)
        gaba_rating = BinaryRating(object_id=synapse.id,
                                   rating_source=consensus_source,
                                   classificationtype=gaba_type,
                                   bool_rating=isGaba)
        db.session.add(gaba_rating)
        issyn = (row.NotSynapse != 1)
        synapse_rating = BinaryRating(object_id=synapse.id,
                                      rating_source=consensus_source,
                                      classificationtype=synapse_type,
                                      bool_rating=issyn)
        db.session.add(synapse_rating)
        isShaft = (row.shaft != 0)
        confidence = np.abs(row.shaft-.5)+.5
        shaft_rating = BinaryRating(object_id=synapse.id,
                                    rating_source=consensus_source,
                                    classificationtype=shaft_type,
                                    bool_rating=isShaft,
                                    confidence=confidence)
        db.session.add(shaft_rating)

        isPre = (row.tdTom == 1) or (row.tdTom == 3)
        isPost = (row.tdTom == 2) or (row.tdTom == 3)
        preRorb_rating = BinaryRating(object_id=synapse.id,
                                      rating_source=consensus_source,
                                      classificationtype=preRorb_type,
                                      bool_rating=isPre)
        postRorb_rating = BinaryRating(object_id=synapse.id,
                                       rating_source=consensus_source,
                                       classificationtype=postRorb_type,
                                       bool_rating=isPost)
        # print(isGaba,issyn,isShaft,isPre,isPost)

        db.session.add(preRorb_rating)
        db.session.add(postRorb_rating)


class InsertRatings(argschema.ArgSchemaParser):
    default_schema = InsertRatingsParameters

    def run(self):
        gaba_type = ClassificationType.query.filter_by(name='GABA').first()
        synapse_type = ClassificationType.query.filter_by(
            name='Synapse').first()
        preRorb_type = ClassificationType.query.filter_by(
            name='preRorb').first()
        postRorb_type = ClassificationType.query.filter_by(
            name='postRorb').first()
        shaft_type = ClassificationType.query.filter_by(name='shaft').first()
        print(gaba_type, synapse_type, preRorb_type, postRorb_type, shaft_type)

        dataset = DataSet.query.filter_by(name=self.args['dataset']).first()
        volume = Volume.query.filter_by(name=self.args['volume'],
                                        dataset=dataset).first()

        metadata_csv = self.args['metadata_csv']
        df = pd.read_csv(metadata_csv, index_col=0,
                         skiprows=1, dtype={'oid': np.object})

        consensus_source = ConsensusSource(
            name=self.args['rating_source_name'])
        db.session.add(consensus_source)
        syncoll_name = self.args['synapse_collection']
        syncoll = SynapseCollection.query.filter_by(volume=volume,
                                                    name=syncoll_name).first()

        print(syncoll)
        for k, row in df.iterrows():
            if str(row.oid) != 'nan':
                insert_synapse_row(row, db, syncoll, consensus_source,
                                   gaba_type, synapse_type, shaft_type,
                                   preRorb_type, postRorb_type)
                # break
        db.session.commit()


if __name__ == '__main__':
    mod = InsertRatings(input_data=example_parameters)
    print(mod.args)
    mod.run()
