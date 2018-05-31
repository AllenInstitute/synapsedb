from setuptools import setup
import synapsedb

with open('requirements.txt', 'r') as f:
    required = f.read().splitlines()

setup(
    version=synapsedb.__version__,
    name='synapsedb',
    description='a flask app for tracking image and annotation data '
                'stored in neuroglancer compatabile data sources, '
                'tracking synapse annotations within those volumes, '
                'and tracking ratings/classification of those synapses',
    author='Forrest Collman',
    author_email='forrestc@alleninstitute.org',
    url='https://github.com/AllenInstitute/synapsedb',
    packages=['synapsedb'],
    include_package_data=True,
    install_requires=required
)
