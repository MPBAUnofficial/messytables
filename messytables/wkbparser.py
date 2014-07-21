import string
import re


def is_hex(val):
    return all(c in string.hexdigits for c in val)


def switch_byte_order(hex_string):
    """
    Convert a big-endian hex string into a little-endian one, and vice versa
    """
    assert ((len(hex_string) % 2) == 0)

    if not is_hex(hex_string):
        raise ValueError('Error: an hexadecimal string was expected.')

    s = ''
    for i in range(len(hex_string), -1, -2):
        s += hex_string[i:i + 2]
    return s


class Geometry(object):
    def __init__(self, geom_type, num_elements=0, srid=-1, has_z=False,
                 has_m=False):
        self.geom_type = geom_type
        self.num_elements = num_elements
        self.srid = srid
        self.has_Z = has_z
        self.has_M = has_m

    @property
    def full_type_name(self):
        return '{0}{1}{2}'.format(
            self.geom_type,
            'Z' if self.has_Z else '',
            'M' if self.has_M else ''
        )

    def __eq__(self, other):
        return (
            self.geom_type == other.geom_type and
            self.num_elements == other.num_elements and
            self.srid == other.srid and
            self.has_Z == other.has_Z and
            self.has_M == other.has_M
        )

    def __repr__(self):
        return '<Geometry ' + self.full_type_name + '>'

    def __str__(self):
        return self.__repr__()

GEOM_TYPES = {
    0x01: 'Point',
    0x02: 'LineString',
    0x03: 'Polygon',
    0x04: 'MultiPoint',
    0x05: 'MultiLineString',
    0x06: 'MultiPolygon',
    0x07: 'GeometryCollection',
    0x08: 'CircularString',
    0x09: 'CompoundCurve',
    0x0A: 'CurvePolygon',
    0x0B: 'MultiCurve',
    0x0C: 'MultiSurface',
    0x0D: 'CurvePolygon',
    0x0E: 'MultiCurve',
    0x0F: 'PolyhedralSurface',
    0x10: 'Tin',
    0x11: 'Triangle'
}


def parse_wkb(value):
    """
    Parse a WKB or EWKB value

    :param value: (e)wkb or (e)wkt value to parse
    :return: parsed geometry
    """
    value = value.strip(' \'\n"').lower()

    if value == '':
        return None

    if not is_hex(value):
        raise ValueError('Error: an hexadecimal string was expected.')

    if value[:2] == '01':  # little endian
        byte_order = 'le'
    elif value[:2] == '00':  # big endian
        byte_order = 'be'
    else:
        raise ValueError('Error: first byte must be either 01 or 00')

    geom_type_hex = value[2:10]
    if byte_order == 'le':
        # convert to big endian
        geom_type_hex = switch_byte_order(geom_type_hex)

    flags = int(geom_type_hex[:2], 16)

    has_z = flags >= 0x80
    if has_z:
        flags -= 0x80

    has_m = flags >= 0x40
    if has_m:
        flags -= 0x40

    has_srid = flags == 0x20

    geom_type_dec = int(geom_type_hex[2:],
                        16)  # actual type code (without previous flag)
    geom_type = GEOM_TYPES.get(geom_type_dec)

    if geom_type is None:
        raise ValueError(
            'Error: invalid geometry type "0x{0:x}"'.format(geom_type_hex)
        )

    srid = -1
    if has_srid:
        srid_hex = value[10:18]
        if byte_order == 'le':
            # convert to big endian
            srid_hex = switch_byte_order(srid_hex)

        srid = int(srid_hex, 16)

    num_elements = 1

    # Geometry 'Point' has an implicit number of elements = 1
    if geom_type_dec > 1:
        num_elements_hex = value[18:26] if has_srid else value[10:18]
        if byte_order == 'le':
            # convert to big endian
            num_elements_hex = switch_byte_order(num_elements_hex)

        num_elements = int(num_elements_hex, 16)

    return Geometry(geom_type, num_elements, srid, has_z, has_m)


def parse_wkt(value):
    # clean the input value from quotes, double quotes etc.
    value = value.strip(' \'\n"').lower().replace('\n', '')

    if value == '':
        return None

    srid = -1
    if value.startswith('srid='):
        srid = int(value.split(';')[0].split('=')[1])
        value = value.split(';')[1]

    regex = r'^(?P<geom_type>[a-zA-Z\s]+)(?P<pts>\((.|\s)+\));?$'
    m = re.match(regex, value)

    if m is None:
        raise ValueError('Error: invalid WKT')

    geom_type = m.group('geom_type')
    geom_type = geom_type.replace(' ', '')

    has_m, has_z = False, False

    if geom_type.endswith('m'):
        has_m = True
        geom_type = geom_type[:-1]

    if geom_type.endswith('z'):
        has_z = True
        geom_type = geom_type[:-1]

    # fixme: I might be broken
    num_elements = m.group('pts').count(',') + 1

    formatted_geom_type = None
    for v in GEOM_TYPES.itervalues():
        if geom_type == v.lower():
            formatted_geom_type = v

    if formatted_geom_type is None:
        raise ValueError('Error: invalid geometry type')

    return Geometry(formatted_geom_type, num_elements, srid, has_z, has_m)