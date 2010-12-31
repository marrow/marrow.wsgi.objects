# encoding: utf-8

import re
import hashlib

from marrow.util.compat import binary, unicode
from marrow.util.object import NoDefault

from marrow.wsgi.objects.adapters.base import *


__all__ = ['ContentLength', 'ContentMD5', 'ContentType', 'Charset']

CHARSET_RE = re.compile(r';\s*charset=([^;]*)', re.I)



class ContentLength(Int):
    def default(self, obj):
        if isinstance(obj.body, binary):
            return len(obj.body)
        
        if isinstance(obj.body, unicode):
            return len(obj.body.encode(obj.encoding))
        
        return -1


class ContentMD5(ReaderWriter):
    def default(self, obj):
        if isinstance(obj.body, binary):
            return hashlib.md5(obj.body).hexdigest()

        if isinstance(obj.body, unicode):
            return hashlib.md5(obj.body.encode(obj.encoding)).hexdigest()

        return None


class ContentType(ReaderWriter):
    """Access the content type, ignoring extended parameters.
    
    If you leave parameters off when assigning a value then existing parameters will be preserved.
    """
    
    default = binary('')
    
    def __get__(self, obj, cls, strip=True):
        value = super(ContentType, self).__get__(obj, cls)
        if not value: return None
        return value.split(';', 1)[0] if strip else value
    
    def __set__(self, obj, value):
        value = binary(value) if value is not None else ''
        
        if ';' not in value:
            original = super(ContentType, self).__get__(obj, None)
            
            if ';' in original:
                value += ';' + original.split(';', 1)[1]
        
        super(ContentType, self).__set__(obj, value)


class Charset(ReaderWriter):
    """Get the charset of the request.

    If the request was sent with a charset parameter on the
    Content-Type, that will be used.  Otherwise if there is a
    default charset (set during construction, or as a class
    attribute) that will be returned.  Otherwise None.

    Setting this property after request instantiation will always
    update Content-Type.  Deleting the property updates the
    Content-Type to remove any charset parameter (if none exists,
    then deleting the property will do nothing, and there will be
    no error).
    """
    
    default = binary('; charset="utf8"')
    
    def __get__(self, obj, cls):
        content_type = super(Charset, self).__get__(obj, cls)
        if not content_type: return None
        
        charset_match = CHARSET_RE.search(content_type)
        
        if charset_match:
            result = charset_match.group(1).strip('"').strip()
            return result
        
        return None
    
    def __set__(self, obj, value):
        if not value:
            self.delete(obj)
            return
        
        value = binary(value)
        content_type = super(Charset, self).__get__(obj, None)
        charset_match = CHARSET_RE.search(content_type) if content_type else None
        
        if charset_match:
            content_type = content_type[:charset_match.start(1)] + value + content_type[charset_match.end(1):]
        
        # TODO: Examine what action browsers take.
        # elif ';' in content_type:
        #     content_type += ', charset="%s"' % charset
        
        elif content_type:
            content_type += '; charset="%s"' % value
        
        else:
            content_type = '; charset="%s"' % value
        
        super(Charset, self).__set__(obj, content_type)
    
    def __delete__(self, obj):
        content_type = CHARSET_RE.sub('', super(Charset, self).__get__(obj, None))
        new_content_type = new_content_type.rstrip().rstrip(';').rstrip(',')
        super(Charset, self).__set__(obj, new_content_type)
