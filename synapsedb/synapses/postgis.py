
from geoalchemy2.functions import GenericFunction
from geoalchemy2 import Geometry


class Box3D(GenericFunction):
    name = 'Box3D'
    type = Geometry


class ST_3DExtent(GenericFunction):
    name = 'ST_3DExtent'
    type = Geometry


class ST_SetSRID(GenericFunction):
    name = 'ST_SetSRID'
    type = Geometry


class ST_XMin(GenericFunction):
    name = 'ST_XMin'
    type = None


class ST_YMin(GenericFunction):
    name = 'ST_YMin'
    type = None


class ST_ZMin(GenericFunction):
    name = 'ST_ZMin'
    type = None


class ST_XMax(GenericFunction):
    name = 'ST_XMax'
    type = None


class ST_YMax(GenericFunction):
    name = 'ST_YMax'
    type = None


class ST_ZMax(GenericFunction):
    name = 'ST_ZMax'
    type = None

class ST_3DMakeBox(GenericFunction):
    name = 'ST_3DMakeBox'
    type = None

class ST_MakePoint(GenericFunction):
    name = 'ST_MakePoint'
    type = None

class ST_Intersects(GenericFunction):
    name = 'ST_Intersects'
    type = None
