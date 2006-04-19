"""form.py: A simple Python form library."""
__author__ = ['Aaron Swartz <me@aaronsw.com>', 'Steve Huffman <http://spez.name/>']
__version__ = '0.22'
__license__ = "Public domain"

import copy, re
import web

def attrget(obj, attr, value=None):
    if hasattr(obj, 'has_key') and obj.has_key(attr): return obj[attr]
    if hasattr(obj, attr): return getattr(obj, attr)
    return value

class Form:
    def __init__(self, *inputs):
        self.inputs = inputs
        self.valid = True

    def __call__(self, x=None):
        o = copy.deepcopy(self)
        if x: o.validates(x)
        return o
    
    def render(self):
        out = ''
        out += '<table>\n'
        for i in self.inputs:
            out += "\t<tr><th><label for='%s'>%s</label></th>" % (i.name, i.description)
            out += "<td>"+i.pre+i.render()+i.post+"</td>"
            out += '<td id="note_%s">%s</td></tr>\n' % (i.name, self.rendernote(i.note))
        out += "</table>"
        return out
    
    def rendernote(self, note):
        if note: return '<strong class="wrong">%s</strong>' % note
        else: return ""

    def validates(self, source=None):
        if source is None: source = web.input()
        out = True
        for i in self.inputs:
            v = attrget(source, i.name)
            out = i.validate(v) and out
        self.valid = out
        return out

    def __getitem__(self, i):
        for x in self.inputs:
            if x.name == i: return x
        raise KeyError, i
    
    def _get_d(self): #@@ should really be form.attr, no?
        return web.storage([(i.name, i.value) for i in self.inputs])
    d = property(_get_d)

class Input(object):
    def __init__(self, name, *validators, **attrs):
        self.description = attrs.pop('description', name)
        self.value = attrs.pop('value', None)
        self.pre = attrs.pop('pre', "")
        self.post = attrs.pop('post', "")
        if 'class_' in attrs:
            attrs['class'] = attrs['class_']
            del attrs['class_']
        self.name, self.validators, self.attrs, self.note = name, validators, attrs, None

    def validate(self, value):
        self.value = value
        for v in self.validators:
            if not v.valid(value):
                self.note = v.msg
                return False
        return True

    def render(self): raise NotImplementedError

    def addatts(self):
        str = ""
        for (n, v) in self.attrs.items():
            str += ' %s="%s"' % (n, web.websafe(v))
        return str
    
#@@ quoting

class Textbox(Input):
    def render(self):
        x = '<input type="text" name="%s"' % web.websafe(self.name)
        if self.value: x += ' value="%s"' % web.websafe(self.value)
        x += self.addatts()
        x += ' />'
        return x

class Password(Input):
    def render(self):
        x = '<input type="password" name="%s"' % web.websafe(self.name)
        if self.value: x += ' value="%s"' % web.websafe(self.value)
        x += self.addatts()
        x += ' />'
        return x

class Textarea(Input):
    def render(self):
        x = '<textarea name="%s"' % web.websafe(self.name)
        x += self.addatts()
        x += '>'
        if self.value is not None: x += web.websafe(self.value)
        x += '</textarea>'
        return x

class Dropdown(Input):
    def __init__(self, name, args, *validators, **attrs):
        self.args = args
        super(Dropdown, self).__init__(name, *validators, **attrs)

    def render(self):
        x = '<select name="%s"%s>\n' % (web.websafe(self.name), self.addatts())
        for arg in self.args:
            if self.value == arg: select_p = ' selected="selected"'
            else: select_p = ''
            x += "  <option"+select_p+">%s</option>\n" % web.websafe(arg)
        x += '</select>\n'
        return x

class Radio(Input):
    def __init__(self, name, args, *validators, **attrs):
        self.args = args
        super(Radio, self).__init__(name, *validators, **attrs)

    def render(self):
        x = '<span>'
        for arg in self.args:
            if self.value == arg: select_p = ' checked="checked"'
            else: select_p = ''
            x += '<input type="radio" name="%s" value="%s"%s%s /> %s ' % (web.websafe(self.name), web.websafe(arg), select_p, self.addatts(), web.websafe(arg))
        return x+'</span>'

class Checkbox(Input):
    def render(self):
        x = '<input name="%s" type="checkbox"' % web.websafe(self.name)
        if self.value: x += ' checked="checked"'
        x += self.addatts()
        x += ' />'
        return x

class Button(Input):
    def render(self):
        safename = web.websafe(self.name)
        x = '<button name="%s"%s>%s</button>' % (safename, self.addatts(), safename)
        return x

class Validator:
    def __deepcopy__(self, memo): return copy.copy(self)
    def __init__(self, msg, test, jstest=None): web.autoassign(self, locals())
    def valid(self, value): 
        try: return self.test(value)
        except: return False

notnull = Validator("Required", bool)

class regexp(Validator):
    def __init__(self, rexp, msg):
        self.rexp = re.compile(rexp)
        self.msg = msg
    
    def valid(self, value):
        return bool(self.rexp.match(value))