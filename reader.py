
import sys
import struct

import opcodes


magic_numbers = [chr(int(mv, 0)) for mv in ['0xCA', '0xFE', '0xBA', '0xBE']]

CP_TYPE_UTF8 = 'CONSTANT_Utf8_info'
CP_TYPE_CLASS = 'CONSTANT_Class'
CP_TYPE_FIELDREF = 'CONSTANT_Fieldref'
CP_TYPE_METHODREF = 'CONSTANT_Methodref'
CP_TYPE_INFMETHREF = 'CONSTANT_InterfaceMethodref'
CP_TYPE_STRING = 'CONSTANT_String'
CP_TYPE_INTEGER = 'CONSTANT_Integer'
CP_TYPE_FLOAT = 'CONSTANT_Float'
CP_TYPE_LONG = 'CONSTANT_Long'
CP_TYPE_DOUBLE = 'CONSTANT_Double'
CP_TYPE_NAMETYPE = 'CONSTANT_NameAndType'


def decode_jutf8(b):
    return b.replace(b'\xC0\x80', b'\x00').decode('utf8')


class CPI(object):

    def __init__(self, *args):
        self.jc = args[0]
        self.tag = args[1]
        self.args = args[2:]


class CPIUTF8(CPI):
    cp_type = CP_TYPE_UTF8

    def __init__(self, jclass, tag, length, bts):
        self.length = length
        self.bytes = bts
        self.value = decode_jutf8(''.join(bts))
        super(CPIUTF8, self).__init__(jclass, tag)

    def __str__(self):
        return u'CP UTF8:"%s"' % self.value


class CPIInt(CPI):
    cp_type = CP_TYPE_INTEGER

    def __init__(self, jclass, tag, value):
        self.value = value
        super(CPIInt, self).__init__(jclass, tag)

    def __str__(self):
        return 'CP int:%s' % self.value


class CPIFloat(CPI):
    cp_type = CP_TYPE_FLOAT

    def __init__(self, jclass, tag, value):
        self.value = value
        super(CPIFloat, self).__init__(jclass, tag)

    def __str__(self):
        return 'CP float:%s' % self.value


class CPILong(CPI):
    cp_type = CP_TYPE_LONG

    def __init__(self, jclass, tag, value):
        self.value = value
        super(CPILong, self).__init__(jclass, tag)

    def __str__(self):
        return 'CP long:%s' % self.value


class CPIDouble(CPI):
    cp_type = CP_TYPE_DOUBLE

    def __init__(self, jclass, tag, value):
        self.value = value
        super(CPIDouble, self).__init__(jclass, tag)

    def __str__(self):
        return 'CP double:%s' % self.value


class CPIClassReference(CPI):
    cp_type = CP_TYPE_CLASS

    def __init__(self, jclass, tag, name_index):
        self.name_index = name_index
        super(CPIClassReference, self).__init__(jclass, tag)

    def get_name(self):
        return self.jc.get_cpi(self.name_index)

    def __str__(self):
        return 'CP class reference index:%s name:%s' % (self.name_index, self.get_name().value)


class CPIStringReference(CPI):
    cp_type = CP_TYPE_STRING

    def __init__(self, jclass, tag, string_index):
        self.string_index = string_index
        super(CPIStringReference, self).__init__(jclass, tag)

    def __str__(self):
        return 'CP string reference index: %s' % self.string_index


class CPIFMI(CPI):

    def __init__(self, jclass, tag, class_index, name_and_type_index):
        self.class_index = class_index
        self.name_and_type_index = name_and_type_index
        super(CPIFMI, self).__init__(jclass, tag)


class CPIFieldReference(CPIFMI):
    cp_type = CP_TYPE_FIELDREF

    def __str__(self):
        return 'CP field reference: class ref %s name and type descriptor %s' %\
               (self.class_index, self.name_and_type_index)


class CPIMethodReference(CPIFMI):
    cp_type = CP_TYPE_METHODREF

    def __str__(self):
        return 'CP method reference: class ref %s name and type descriptor %s' %\
               (self.class_index, self.name_and_type_index)


class CPIInterfaceReference(CPIFMI):
    cp_type = CP_TYPE_INFMETHREF

    def __str__(self):
        return 'CP interface reference: class ref %s name and type descriptor %s' %\
            (self.class_index, self.name_and_type_index)


class CPINameAndTypeDescriptor(CPI):
    cp_type = CP_TYPE_NAMETYPE

    def __init__(self, jclass, tag, name_index, descriptor_index):
        self.name_index = name_index
        self.descriptor_index = descriptor_index
        super(CPINameAndTypeDescriptor, self).__init__(jclass, tag)

    def __str__(self):
        return 'CP name and type descriptor: name index %s type index %s' % (
            self.name_index, self.descriptor_index)


class AttributeInfo(object):

    def __init__(self, jclass, attribute_name_index):
        self.jc = jclass
        self.attribute_name_index = attribute_name_index
        self.attribute_length = jclass.read_uint32()

    @property
    def name(self):
        return self.jc.cpi_val(self.attribute_name_index)

    def __str__(self):
        return 'Attribute: %s' % self.name

    def __repr__(self):
        return self.__str__()


class AttributeConstantValue(AttributeInfo):

    def __init__(self, jclass, attribute_name_index):
        super(AttributeConstantValue, self).__init__(jclass, attribute_name_index)
        self.constantvalue_index = jclass.read_uint16()

    @property
    def value(self):
        return self.jc.cpi_val(self.constantvalue_index)

    def __str__(self):
        return "%s %s" % (super(AttributeConstantValue, self), self.value)


class ExceptionItem(object):

    def __init__(self, jclass):
        self.start_pc = jclass.read_uint16()
        self.end_pc = jclass.read_uint16()
        self.handler = jclass.read_uint16()
        self.catch = jclass.read_uint16()


class AttributeCode(AttributeInfo):

    def __init__(self, jclass, attribute_name_index):
        super(AttributeCode, self).__init__(jclass, attribute_name_index)
        self.max_stack = jclass.read_uint16()
        self.max_locals = jclass.read_uint16()
        self.code_length = jclass.read_uint32()
        self.code = [jclass.read_uint8() for _ in xrange(self.code_length)]
        self.exception_table_length = jclass.read_uint16()
        self.exception_table = [ExceptionItem(jclass) for _ in xrange(self.exception_table_length)]
        self.attributes_count = jclass.read_uint16()
        self.attributes = [make_attribute_info(jclass) for _ in xrange(self.attributes_count)]

    @property
    def opcodes(self):
        return opcodes.decode(self.code)

    def __str__(self):
        return "%s %s" % (super(AttributeCode, self).__str__(), self.opcodes)


class AttributeException(AttributeInfo):

    def __init__(self, jclass, attribute_name_index):
        super(AttributeException, self).__init__(jclass, attribute_name_index)
        self.number_of_exceptions = jclass.read_uint16()
        self.exception_index_table = [jclass.read_uint16() for _ in xrange(self.number_of_exceptions)]


class InnerClass(object):

    def __init__(self, jclass):
        self.inner_class_info_index = jclass.read_uint16()
        self.outer_class_info_index = jclass.read_uint16()
        self.inner_name_index = jclass.read_uint16()
        self.inner_class_access_flags = jclass.read_uint16()


class AttributeInnerClasses(AttributeInfo):

    def __init__(self, jclass, attribute_name_index):
        super(AttributeInnerClasses, self).__init__(jclass, attribute_name_index)
        self.number_of_classes = jclass.read_uint16()
        self.classes = [InnerClass(jclass) for _ in xrange(self.number_of_classes)]


class AttributeSynthetic(AttributeInfo):

    def __init__(self, jclass, attribute_name_index):
        super(AttributeSynthetic, self).__init__(jclass, attribute_name_index)


class AttributeSourceFile(AttributeInfo):

    def __init__(self, jclass, attribute_name_index):
        super(AttributeSourceFile, self).__init__(jclass, attribute_name_index)
        self.sourcefile_index = jclass.read_uint16()


class LineNumber(object):

    def __init__(self, jclass):
        self.start_pc = jclass.read_uint16()
        self.line_number = jclass.read_uint16()


class AttributeLineNumberTable(AttributeInfo):

    def __init__(self, jclass, attribute_name_index):
        super(AttributeLineNumberTable, self).__init__(jclass, attribute_name_index)
        self.line_number_table_length = jclass.read_uint16()
        self.line_number_table = [LineNumber(jclass) for _ in xrange(self.line_number_table_length)]


class LocalVariable(object):

    def __init__(self, jclass):
        self.start_pc = jclass.read_uint16()
        self.length = jclass.read_uint16()
        self.name_index = jclass.read_uint16()
        self.descriptor_index = jclass.read_uint16()
        self.index = jclass.read_uint16()


class AttributeLocalVariableTable(AttributeInfo):

    def __init__(self, jclass, attribute_name_index):
        super(AttributeLocalVariableTable, self).__init__(jclass, attribute_name_index)
        self.local_variable_table_length = jclass.read_uint16()
        self.local_variable_table = [LocalVariable(jclass) for _ in xrange(self.local_variable_table_length)]


class AttributeDeprecated(AttributeInfo):

    def __init__(self, jclass, attribute_name_index):
        super(AttributeDeprecated, self).__init__(jclass, attribute_name_index)


class AttributeOther(AttributeInfo):

    def __init__(self, jclass, attribute_name_index):
        super(AttributeOther, self).__init__(jclass, attribute_name_index)
        self.info = [jclass.read_uint8() for _ in xrange(self.attribute_length)]


def make_attribute_info(jclass):
    attribute_name_index = jclass.read_uint16()
    name = jclass.get_cpi(attribute_name_index).value
    if name == 'ConstantValue':
        cl = AttributeConstantValue
    elif name == 'Code':
        cl = AttributeCode
    elif name == 'Exceptions':
        cl = AttributeException
    elif name == 'InnerClasses':
        cl = AttributeInnerClasses
    elif name == 'Synthetic':
        cl = AttributeSynthetic
    elif name == 'SourceFile':
        cl = AttributeSourceFile
    elif name == 'LineNumberTable':
        cl = AttributeLineNumberTable
    elif name == 'LocalVariableTable':
        cl = AttributeLocalVariableTable
    elif name == 'Deprecated':
        cl = AttributeDeprecated
    else:
        cl = AttributeOther
    return cl(jclass, attribute_name_index)


class FieldInfo(object):

    def __init__(self, jclass):
        self.jc = jclass
        self.access_flags = jclass.read_uint16()
        self.name_index = jclass.read_uint16()
        self.descriptor_index = jclass.read_uint16()
        self.attributes_count = jclass.read_uint16()
        self.attributes = [make_attribute_info(jclass) for _ in xrange(self.attributes_count)]

    def __str__(self):
        return 'Field attrs:%s name:%s desc:%s att:%s' %\
               (self.attributes_count, self.jc.cpi_val(self.name_index),
                self.jc.cpi_val(self.descriptor_index), self.attributes)


class MethodInfo(object):

    def __init__(self, jclass):
        self.jc = jclass
        self.access_flags = jclass.read_uint16()
        self.name_index = jclass.read_uint16()
        self.descriptor_index = jclass.read_uint16()
        self.attributes_count = jclass.read_uint16()
        self.attributes = [make_attribute_info(jclass) for _ in xrange(self.attributes_count)]

    def __str__(self):
        return 'Method attrs:%s name:%s desc:%s att:%s' %\
               (self.attributes_count, self.jc.cpi_val(self.name_index),
                self.jc.cpi_val(self.descriptor_index), self.attributes)


# noinspection PyAttributeOutsideInit
class JavaClass(object):

    def __init__(self, byte_array, validate=False):
        self.ba = byte_array
        self.to_validate = validate
        self.ba_data = iter(self.ba)
        self.constant_pool = []
        self.minor_version = None
        self.major_version = None
        self.constant_pool_size = None

    def version2string(self):
        names = {49: 'J2SE 5.0',
                 50: 'J2SE 6.0',
                 51: 'J2SE 7',
                 52: 'J2SE 8'
                 }
        return names[self.major_version]

    def read_char(self):
        return self.ba_data.next()

    def read_chars(self, count):
        return [self.read_char() for _ in xrange(count)]

    def unpack(self, fmt, size=1):
        if size == 1:
            data = self.read_char()
        else:
            data = ''.join(self.read_chars(size))
        return struct.unpack(fmt, data)[0]

    def read_int8(self):
        return self.unpack('>b')

    def read_uint8(self):
        return self.unpack('>B')

    def read_uint16(self):
        return self.unpack('>H', 2)

    def read_int16(self):
        return self.unpack('>h', 2)

    def read_uint32(self):
        return self.unpack('>I', 4)

    def read_int32(self):
        return self.unpack('>i', 4)

    def read_float32(self):
        return self.unpack('f', 4)

    def read_double64(self):
        return self.unpack('d', 8)

    def read_int64(self):
        return self.unpack('>q', 8)

    def get_cpi(self, i):
        return self.constant_pool[i - 1]

    def cpi_val(self, i):
        return self.constant_pool[i - 1].value

    def read_constant_pool(self):
        i = 1
        while i < self.constant_pool_size:
            v = self.read_uint8()
            if v == 1:
                pv = self.read_uint16()
                self.constant_pool.append(CPIUTF8(self, v, pv, self.read_chars(pv)))
            elif v == 3:
                self.constant_pool.append(CPIInt(self, v, self.read_int32()))
            elif v == 4:
                self.constant_pool.append(CPIFloat(self, v, self.read_float32()))
            elif v == 5:
                self.constant_pool.append(CPILong(self, v, self.read_int64()))
                i += 1
            elif v == 6:
                self.constant_pool.append(CPIDouble(self, v, self.read_double64()))
                i += 1
            elif v == 7:
                self.constant_pool.append(CPIClassReference(self, v, self.read_uint16()))
            elif v == 8:
                self.constant_pool.append(CPIStringReference(self, v, self.read_uint16()))
            elif v == 9:
                self.constant_pool.append(CPIFieldReference(self, v, self.read_uint16(), self.read_uint16()))
            elif v == 10:
                self.constant_pool.append(CPIMethodReference(self, v, self.read_uint16(), self.read_uint16()))
            elif v == 11:
                self.constant_pool.append(
                    CPIInterfaceReference(
                        self,
                        v,
                        self.read_uint16(),
                        self.read_uint16()))
            elif v == 12:
                self.constant_pool.append(
                    CPINameAndTypeDescriptor(
                        self,
                        v,
                        self.read_uint16(),
                        self.read_uint16()))
            else:
                raise Exception('constant pool unknown tag byte %s' % v)
            i += 1

    def read_interfaces(self):
        self.interfaces = [self.read_int16() for _ in xrange(self.interfaces_count)]

    def read_fields(self):
        self.fields = [FieldInfo(self) for _ in xrange(self.fields_count)]

    def read_methods(self):
        self.methods = [MethodInfo(self) for _ in xrange(self.methods_count)]

    def read_attributes(self):
        self.attributes = [make_attribute_info(self) for _ in xrange(self.attributes_count)]

    def decode(self):
        mn = self.read_chars(4)
        if mn != magic_numbers:
            raise Exception('magic numbers %s do not match %s' % (magic_numbers, mn))
        self.minor_version = self.read_uint16()
        self.major_version = self.read_uint16()
        self.constant_pool_size = self.read_uint16()
        self.read_constant_pool()
        self.access_flags = self.read_uint16()
        self.this_class = self.read_uint16()
        self.super_class = self.read_uint16()
        self.interfaces_count = self.read_uint16()
        self.read_interfaces()
        self.fields_count = self.read_uint16()
        self.read_fields()
        self.methods_count = self.read_uint16()
        self.read_methods()
        self.attributes_count = self.read_uint16()
        self.read_attributes()

    def print_out(self):
        print 'minor version: %s' % self.minor_version
        print 'major version: %s %s' % (self.major_version, self.version2string())
        print 'pool size: %s' % self.constant_pool_size
        for cpi in self.constant_pool:
            print cpi
        print 'access flags: %s' % self.access_flags
        print 'this class index: %s' % self.this_class
        print self.get_cpi(self.this_class)
        print 'super class index: %s' % self.super_class
        print self.get_cpi(self.super_class)
        print 'interfaces count: %s' % self.interfaces_count
        for ifc in self.interfaces:
            print ifc
        print 'fields count: %s' % self.fields_count
        for fld in self.fields:
            print fld
        print 'methods count: %s' % self.methods_count
        for mtd in self.methods:
            print mtd
        print 'attributes count: %s' % self.attributes_count
        for att in self.attributes:
            print att


with open(sys.argv[1]) as f:
    jc = JavaClass(f.read())
    jc.decode()
    jc.print_out()
