from setuptools import setup

setup(
    name='synapsedb',
    packages=['synapsedb'],
    include_package_data=True,
    install_requires=[
        'flask',
    ],
)