# -*- coding: utf-8 -*-

""" Utilities

    @requires: U{B{I{gluon}} <http://web2py.com>}

    @copyright: (c) 2010-2021 Sahana Software Foundation
    @license: MIT

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following
    conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.
"""

import collections
import copy
import os
import sys

from html.parser import HTMLParser
from urllib import parse as urlparse

from gluon import current, redirect, HTTP, URL, \
                  A, BEAUTIFY, CODE, DIV, PRE, SPAN, TABLE, TAG, TR, XML, \
                  IS_EMPTY_OR, IS_NOT_IN_DB
from gluon.storage import Storage
from gluon.tools import addrow

from s3dal import Expression, Field, Row, S3DAL

from .convert import s3_str

# Compact JSON encoding
SEPARATORS = (",", ":")

RCVARS = "rcvars"

# =============================================================================
def s3_get_last_record_id(tablename):
    """
        Reads the last record ID for a resource from a session

        @param table: the the tablename
    """

    session = current.session

    if RCVARS in session and tablename in session[RCVARS]:
        return session[RCVARS][tablename]
    else:
        return None

# =============================================================================
def s3_store_last_record_id(tablename, record_id):
    """
        Stores a record ID for a resource in a session

        @param tablename: the tablename
        @param record_id: the record ID to store
    """

    session = current.session

    # Web2py type "Reference" can't be pickled in session (no crash,
    # but renders the server unresponsive) => always convert into int
    try:
        record_id = int(record_id)
    except ValueError:
        return False

    if RCVARS not in session:
        session[RCVARS] = Storage({tablename: record_id})
    else:
        session[RCVARS][tablename] = record_id
    return True

# =============================================================================
def s3_remove_last_record_id(tablename=None):
    """
        Clears one or all last record IDs stored in a session

        @param tablename: the tablename, None to remove all last record IDs
    """

    session = current.session

    if tablename:
        if RCVARS in session and tablename in session[RCVARS]:
            del session[RCVARS][tablename]
    else:
        if RCVARS in session:
            del session[RCVARS]
    return True

# =============================================================================
def s3_validate(table, field, value, record=None):
    """
        Validates a value for a field

        @param table: Table
        @param field: Field or name of the field
        @param value: value to validate
        @param record: the existing database record, if available

        @return: tuple (value, error)
    """

    default = (value, None)

    if isinstance(field, str):
        fieldname = field
        if fieldname in table.fields:
            field = table[fieldname]
        else:
            return default
    else:
        fieldname = field.name

    self_id = None

    if record is not None:

        try:
            v = record[field]
        except: # KeyError is now AttributeError
            v = None
        if v and v == value:
            return default

        try:
            self_id = record[table._id]
        except: # KeyError is now AttributeError
            pass

    requires = field.requires

    if field.unique and not requires:
        # Prevent unique-constraint violations
        field.requires = IS_NOT_IN_DB(current.db, str(field))
        if self_id:
            field.requires.set_self_id(self_id)

    elif self_id:

        # Initialize all validators for self_id
        if not isinstance(requires, (list, tuple)):
            requires = [requires]
        for r in requires:
            if hasattr(r, "set_self_id"):
                r.set_self_id(self_id)
            if hasattr(r, "other") and \
               hasattr(r.other, "set_self_id"):
                r.other.set_self_id(self_id)

    try:
        value, error = field.validate(value)
    except:
        # Oops - something went wrong in the validator:
        # write out a debug message, and continue anyway
        current.log.error("Validate %s: %s (ignored)" %
                          (field, sys.exc_info()[1]))
        return (None, None)
    else:
        return (value, error)

# =============================================================================
def s3_represent_value(field,
                       value = None,
                       record = None,
                       linkto = None,
                       strip_markup = False,
                       xml_escape = False,
                       non_xml_output = False,
                       extended_comments = False
                       ):
    """
        Represent a field value

        @param field: the field (Field)
        @param value: the value
        @param record: record to retrieve the value from
        @param linkto: function or format string to link an ID column
        @param strip_markup: strip away markup from representation
        @param xml_escape: XML-escape the output
        @param non_xml_output: Needed for output such as pdf or xls
        @param extended_comments: Typically the comments are abbreviated
    """

    xml_encode = current.xml.xml_encode

    NONE = current.response.s3.crud_labels["NONE"]
    cache = current.cache
    fname = field.name

    # Get the value
    if record is not None:
        tablename = str(field.table)
        if tablename in record and isinstance(record[tablename], Row):
            text = val = record[tablename][field.name]
        else:
            text = val = record[field.name]
    else:
        text = val = value

    ftype = str(field.type)
    if ftype[:5] == "list:" and not isinstance(val, list):
        # Default list representation can't handle single values
        val = [val]

    # Always XML-escape content markup if it is intended for xml output
    # This code is needed (for example) for a data table that includes a link
    # Such a table can be seen at inv/inv_item
    # where the table displays a link to the warehouse
    if not non_xml_output:
        if not xml_escape and val is not None:
            if ftype in ("string", "text"):
                val = text = xml_encode(s3_str(val))
            elif ftype == "list:string":
                val = text = [xml_encode(s3_str(v)) for v in val]

    # Get text representation
    if field.represent:
        try:
            key = s3_str("%s_repr_%s" % (field, val))
        except (UnicodeEncodeError, UnicodeDecodeError):
            text = field.represent(val)
        else:
            text = cache.ram(key,
                             lambda: field.represent(val),
                             time_expire = 60,
                             )
        if isinstance(text, DIV):
            text = str(text)
        elif not isinstance(text, str):
            text = s3_str(text)
    else:
        if val is None:
            text = NONE
        elif fname == "comments" and not extended_comments:
            ur = s3_str(text)
            if len(ur) > 48:
                text = s3_str("%s..." % ur[:45])
        else:
            text = s3_str(text)

    # Strip away markup from text
    if strip_markup and "<" in text:
        try:
            stripper = S3MarkupStripper()
            stripper.feed(text)
            text = stripper.stripped()
        except:
            pass

    # Link ID field
    if fname == "id" and linkto:
        link_id = str(val)
        try:
            href = linkto(link_id)
        except TypeError:
            href = linkto % link_id
        href = str(href).replace(".aadata", "")
        return A(text, _href=href).xml()

    # XML-escape text
    elif xml_escape:
        text = xml_encode(text)

    #try:
    #    text = text.decode("utf-8")
    #except:
    #    pass

    return text

# =============================================================================
def s3_dev_toolbar():
    """
        Developer Toolbar - ported from gluon.Response.toolbar()
        Shows useful stuff at the bottom of the page in Debug mode
    """

    from gluon.dal import DAL
    from gluon.utils import web2py_uuid

    #admin = URL("admin", "default", "design", extension="html",
    #            args=current.request.application)
    BUTTON = TAG.button

    dbstats = []
    dbtables = {}
    infos = DAL.get_instances()
    for k, v in infos.items():
        dbstats.append(TABLE(*[TR(PRE(row[0]), "%.2fms" %
                                      (row[1] * 1000))
                                       for row in v["dbstats"]]))
        dbtables[k] = {"defined": v["dbtables"]["defined"] or "[no defined tables]",
                       "lazy": v["dbtables"]["lazy"] or "[no lazy tables]",
                       }

    u = web2py_uuid()
    backtotop = A("Back to top", _href="#totop-%s" % u)
    # Convert lazy request.vars from property to Storage so they
    # will be displayed in the toolbar.
    request = copy.copy(current.request)
    request.update(vars=current.request.vars,
                   get_vars=current.request.get_vars,
                   post_vars=current.request.post_vars)

    # Filter out sensitive session details
    def no_sensitives(key):
        if key in ("hmac_key", "password") or \
           key[:8] == "_formkey" or \
           key[-4:] == "_key" or \
           key[-5:] == "token":
            return None
        return key

    return DIV(
        #BUTTON("design", _onclick="document.location='%s'" % admin),
        BUTTON("request",
               _onclick="$('#request-%s').slideToggle().removeClass('hide')" % u),
        #BUTTON("response",
        #       _onclick="$('#response-%s').slideToggle().removeClass('hide')" % u),
        BUTTON("session",
               _onclick="$('#session-%s').slideToggle().removeClass('hide')" % u),
        BUTTON("db tables",
               _onclick="$('#db-tables-%s').slideToggle().removeClass('hide')" % u),
        BUTTON("db stats",
               _onclick="$('#db-stats-%s').slideToggle().removeClass('hide')" % u),
        DIV(BEAUTIFY(request), backtotop,
            _class="hide", _id="request-%s" % u),
        #DIV(BEAUTIFY(current.response), backtotop,
        #    _class="hide", _id="response-%s" % u),
        DIV(BEAUTIFY(current.session, keyfilter=no_sensitives), backtotop,
            _class="hide", _id="session-%s" % u),
        DIV(BEAUTIFY(dbtables), backtotop,
            _class="hide", _id="db-tables-%s" % u),
        DIV(BEAUTIFY(dbstats), backtotop,
            _class="hide", _id="db-stats-%s" % u),
        _id="totop-%s" % u
    )

# =============================================================================
def s3_required_label(field_label):
    """ Default HTML for labels of required form fields """

    return TAG[""]("%s:" % field_label, SPAN(" *", _class="req"))

# =============================================================================
def s3_mark_required(fields,
                     mark_required=None,
                     label_html=None,
                     map_names=None):
    """
        Add asterisk to field label if a field is required

        @param fields: list of fields (or a table)
        @param mark_required: list of field names which are always required
        @param label_html: function to render labels of requried fields
        @param map_names: dict of alternative field names and labels
                          {fname: (name, label)}, used for inline components
        @return: tuple, (dict of form labels, has_required) with has_required
                 indicating whether there are required fields in this form
    """

    if not mark_required:
        mark_required = ()

    if label_html is None:
        # @ToDo: DRY this setting with s3.ui.locationselector.js
        label_html = s3_required_label

    labels = {}

    # Do we have any required fields?
    _required = False
    for field in fields:
        if map_names:
            fname, flabel = map_names[field.name]
        else:
            fname, flabel = field.name, field.label
        if not flabel:
            labels[fname] = ""
            continue
        if field.writable:
            validators = field.requires
            if isinstance(validators, IS_EMPTY_OR) and field.name not in mark_required:
                # Allow notnull fields to be marked as not required
                # if we populate them onvalidation
                labels[fname] = "%s:" % flabel
                continue
            else:
                required = field.required or field.notnull or \
                            field.name in mark_required
            if not validators and not required:
                labels[fname] = "%s:" % flabel
                continue
            if not required:
                if not isinstance(validators, (list, tuple)):
                    validators = [validators]
                for v in validators:
                    if hasattr(v, "options"):
                        if hasattr(v, "zero") and v.zero is None:
                            continue
                    if hasattr(v, "mark_required"):
                        if v.mark_required:
                            required = True
                            break
                        else:
                            continue
                    try:
                        error = v("")[1]
                    except TypeError:
                        # default validator takes no args
                        pass
                    else:
                        if error:
                            required = True
                            break
            if required:
                _required = True
                labels[fname] = label_html(flabel)
            else:
                labels[fname] = "%s:" % flabel
        else:
            labels[fname] = "%s:" % flabel

    return (labels, _required)

# =============================================================================
def s3_addrow(form, label, widget, comment, formstyle, row_id, position=-1):
    """
        Add a row to a form, applying formstyle

        @param form: the FORM
        @param label: the label
        @param widget: the widget
        @param comment: the comment
        @param formstyle: the formstyle
        @param row_id: the form row HTML id
        @param position: position where to insert the row
    """

    if callable(formstyle):
        row = formstyle(row_id, label, widget, comment)
        if isinstance(row, (tuple, list)):
            for subrow in row:
                form[0].insert(position, subrow)
                if position >= 0:
                    position += 1
        else:
            form[0].insert(position, row)
    else:
        addrow(form, label, widget, comment, formstyle, row_id,
               position = position)
    return

# =============================================================================
def s3_keep_messages():
    """
        Retain user messages from previous request - prevents the messages
        from being swallowed by overhanging Ajax requests or intermediate
        pages with mandatory redirection (see s3_redirect_default)
    """

    response = current.response
    session = current.session

    session.confirmation = response.confirmation
    session.error = response.error
    session.flash = response.flash
    session.information = response.information
    session.warning = response.warning

# =============================================================================
def s3_redirect_default(location="", how=303, client_side=False, headers=None):
    """
        Redirect preserving response messages, useful when redirecting from
        index() controllers.

        @param location: the url where to redirect
        @param how: what HTTP status code to use when redirecting
        @param client_side: if set to True, it triggers a reload of
                            the entire page when the fragment has been
                            loaded as a component
        @param headers: response headers
    """

    s3_keep_messages()

    redirect(location,
             how=how,
             client_side=client_side,
             headers=headers,
             )

# =============================================================================
def s3_include_debug_css():
    """
        Generates html to include the css listed in
            /modules/templates/<theme>/css.cfg
    """

    request = current.request

    location = current.response.s3.theme_config
    filename = "%s/modules/templates/%s/css.cfg" % (request.folder, location)
    if not os.path.isfile(filename):
        raise HTTP(500, "Theme configuration file missing: modules/templates/%s/css.cfg" % location)

    link_template = '<link href="/%s/static/styles/%%s" rel="stylesheet" type="text/css" />' % \
                    request.application
    links = ""

    with open(filename, "r") as css_cfg:
        links = "\n".join(link_template % cssname.rstrip()
                          for cssname in css_cfg if cssname[0] != "#")

    return XML(links)

# =============================================================================
def s3_include_debug_js():
    """
        Generates html to include the js scripts listed in
            /static/scripts/tools/sahana.js.cfg
    """

    request = current.request

    scripts_dir = os.path.join(request.folder, "static", "scripts")
    sys.path.append(os.path.join(scripts_dir, "tools"))

    import mergejsmf

    configDictCore = {
        ".": scripts_dir,
        "ui": scripts_dir,
        "web2py": scripts_dir,
        "S3":     scripts_dir
    }
    configFilename = "%s/tools/sahana.js.cfg"  % scripts_dir
    files = mergejsmf.getFiles(configDictCore, configFilename)[1]

    script_template = '<script src="/%s/static/scripts/%%s"></script>' % \
                      request.application

    scripts = "\n".join(script_template % scriptname for scriptname in files)
    return XML(scripts)

# =============================================================================
def s3_include_ext():
    """
        Add ExtJS CSS & JS into a page for a Map
        - since this is normally run from MAP.xml() it is too late to insert into
          s3.[external_]stylesheets, so must inject sheets into correct order
    """

    s3 = current.response.s3
    if s3.ext_included:
        # Ext already included
        return
    request = current.request
    appname = request.application

    xtheme = current.deployment_settings.get_base_xtheme()
    if xtheme:
        xtheme = "%smin.css" % xtheme[:-3]
        xtheme = \
    "<link href='/%s/static/themes/%s' rel='stylesheet' type='text/css' />" % \
        (appname, xtheme)

    if s3.cdn:
        # For Sites Hosted on the Public Internet, using a CDN may provide better performance
        PATH = "//cdn.sencha.com/ext/gpl/3.4.1.1"
    else:
        PATH = "/%s/static/scripts/ext" % appname

    if s3.debug:
        # Provide debug versions of CSS / JS
        adapter = "%s/adapter/jquery/ext-jquery-adapter-debug.js" % PATH
        main_js = "%s/ext-all-debug.js" % PATH
        main_css = \
    "<link href='%s/resources/css/ext-all-notheme.css' rel='stylesheet' type='text/css' />" % PATH
        if not xtheme:
            xtheme = \
    "<link href='%s/resources/css/xtheme-gray.css' rel='stylesheet' type='text/css' />" % PATH
    else:
        adapter = "%s/adapter/jquery/ext-jquery-adapter.js" % PATH
        main_js = "%s/ext-all.js" % PATH
        if xtheme:
            main_css = \
    "<link href='/%s/static/scripts/ext/resources/css/ext-notheme.min.css' rel='stylesheet' type='text/css' />" % appname
        else:
            main_css = \
    "<link href='/%s/static/scripts/ext/resources/css/ext-gray.min.css' rel='stylesheet' type='text/css' />" % appname

    scripts = s3.scripts
    scripts_append = scripts.append
    scripts_append(adapter)
    scripts_append(main_js)

    langfile = "ext-lang-%s.js" % s3.language
    if os.path.exists(os.path.join(request.folder, "static", "scripts", "ext", "src", "locale", langfile)):
        locale = "%s/src/locale/%s" % (PATH, langfile)
        scripts_append(locale)

    if xtheme:
        s3.jquery_ready.append('''$('link:first').after("%s").after("%s")''' % (xtheme, main_css))
    else:
        s3.jquery_ready.append('''$('link:first').after("%s")''' % main_css)
    s3.ext_included = True

# =============================================================================
def s3_include_simile():
    """
        Add Simile CSS & JS into a page for a Timeline
    """

    s3 = current.response.s3
    if s3.simile_included:
        # Simile already included
        return
    appname = current.request.application

    scripts = s3.scripts

    if s3.debug:
        # Provide debug versions of CSS / JS
        s3.scripts += ["/%s/static/scripts/S3/s3.simile.js" % appname,
                       "/%s/static/scripts/simile/ajax/scripts/platform.js" % appname,
                       "/%s/static/scripts/simile/ajax/scripts/debug.js" % appname,
                       "/%s/static/scripts/simile/ajax/scripts/xmlhttp.js" % appname,
                       "/%s/static/scripts/simile/ajax/scripts/json.js" % appname,
                       "/%s/static/scripts/simile/ajax/scripts/dom.js" % appname,
                       "/%s/static/scripts/simile/ajax/scripts/graphics.js" % appname,
                       "/%s/static/scripts/simile/ajax/scripts/date-time.js" % appname,
                       "/%s/static/scripts/simile/ajax/scripts/string.js" % appname,
                       "/%s/static/scripts/simile/ajax/scripts/html.js" % appname,
                       "/%s/static/scripts/simile/ajax/scripts/data-structure.js" % appname,
                       "/%s/static/scripts/simile/ajax/scripts/units.js" % appname,
                       "/%s/static/scripts/simile/ajax/scripts/ajax.js" % appname,
                       "/%s/static/scripts/simile/ajax/scripts/history.js" % appname,
                       "/%s/static/scripts/simile/ajax/scripts/window-manager.js" % appname,
                       "/%s/static/scripts/simile/ajax/scripts/remoteLog.js" % appname,
                       "/%s/static/scripts/S3/s3.timeline.js" % appname,
                       "/%s/static/scripts/simile/timeline/scripts/timeline.js" % appname,
                       "/%s/static/scripts/simile/timeline/scripts/band.js" % appname,
                       "/%s/static/scripts/simile/timeline/scripts/themes.js" % appname,
                       "/%s/static/scripts/simile/timeline/scripts/ethers.js" % appname,
                       "/%s/static/scripts/simile/timeline/scripts/ether-painters.js" % appname,
                       "/%s/static/scripts/simile/timeline/scripts/event-utils.js" % appname,
                       "/%s/static/scripts/simile/timeline/scripts/labellers.js" % appname,
                       "/%s/static/scripts/simile/timeline/scripts/sources.js" % appname,
                       "/%s/static/scripts/simile/timeline/scripts/original-painter.js" % appname,
                       "/%s/static/scripts/simile/timeline/scripts/detailed-painter.js" % appname,
                       "/%s/static/scripts/simile/timeline/scripts/overview-painter.js" % appname,
                       "/%s/static/scripts/simile/timeline/scripts/compact-painter.js" % appname,
                       "/%s/static/scripts/simile/timeline/scripts/decorators.js" % appname,
                       "/%s/static/scripts/simile/timeline/scripts/l10n/en/timeline.js" % appname,
                       "/%s/static/scripts/simile/timeline/scripts/l10n/en/labellers.js" % appname,
                       ]
        css = "".join(["<link href='/%s/static/scripts/simile/ajax/styles/graphics.css' rel='stylesheet' type='text/css' />" % appname,
                       "<link href='/%s/static/scripts/simile/timeline/styles/ethers.css' rel='stylesheet' type='text/css' />" % appname,
                       "<link href='/%s/static/scripts/simile/timeline/styles/events.css' rel='stylesheet' type='text/css' />" % appname,
                       "<link href='/%s/static/scripts/simile/timeline/styles/timeline.css' rel='stylesheet' type='text/css' />" % appname,
                       ])
    else:
        s3.scripts.append("/%s/static/scripts/S3/s3.timeline.min.js" % appname)
        css = "".join(["<link href='/%s/static/scripts/simile/ajax/styles/graphics.css' rel='stylesheet' type='text/css' />" % appname,
                       "<link href='/%s/static/scripts/simile/timeline/timeline-bundle.css' rel='stylesheet' type='text/css' />" % appname,
                       ])

    s3.jquery_ready.append('''$('link:first').after("%s")''' % css)

    supported_locales = [
        "cs",       # Czech
        "de",       # German
        "en",       # English
        "es",       # Spanish
        "fr",       # French
        "it",       # Italian
        "nl",       # Dutch (The Netherlands)
        "pl",       # Polish
        "ru",       # Russian
        "se",       # Swedish
        "tr",       # Turkish
        "vi",       # Vietnamese
        "zh"        # Chinese
        ]

    if s3.language in supported_locales:
        locale = s3.language
    else:
        locale = "en"
    s3.scripts += ["/%s/static/scripts/simile/timeline/scripts/l10n/%s/timeline.js" % (appname, locale),
                   "/%s/static/scripts/simile/timeline/scripts/l10n/%s/labellers.js" % (appname, locale),
                   ]

    s3.simile_included = True

# =============================================================================
def s3_include_underscore():
    """
        Add Undercore JS into a page
        - for Map templates
        - for templates in GroupedOptsWidget comment
    """

    s3 = current.response.s3
    debug = s3.debug
    scripts = s3.scripts
    if s3.cdn:
        if debug:
            script = \
"//cdnjs.cloudflare.com/ajax/libs/underscore.js/1.6.0/underscore.js"
        else:
            script = \
"//cdnjs.cloudflare.com/ajax/libs/underscore.js/1.6.0/underscore-min.js"
    else:
        if debug:
            script = URL(c="static", f="scripts/underscore.js")
        else:
            script = URL(c="static", f="scripts/underscore-min.js")
    if script not in scripts:
        scripts.append(script)

# =============================================================================
def s3_has_foreign_key(field, m2m=True):
    """
        Check whether a field contains a foreign key constraint

        @param field: the field (Field instance)
        @param m2m: also detect many-to-many links

        @note: many-to-many references (list:reference) are not DB constraints,
               but pseudo-references implemented by the DAL. If you only want
               to find real foreign key constraints, then set m2m=False.
    """

    try:
        ftype = str(field.type)
    except:
        # Virtual Field
        return False

    if ftype[:9] == "reference" or \
       m2m and ftype[:14] == "list:reference" or \
       current.s3db.virtual_reference(field):
        return True

    return False

# =============================================================================
def s3_get_foreign_key(field, m2m=True):
    """
        Resolve a field type into the name of the referenced table,
        the referenced key and the reference type (M:1 or M:N)

        @param field: the field (Field instance)
        @param m2m: also detect many-to-many references

        @return: tuple (tablename, key, multiple), where tablename is
                 the name of the referenced table (or None if this field
                 has no foreign key constraint), key is the field name of
                 the referenced key, and multiple indicates whether this is
                 a many-to-many reference (list:reference) or not.

        @note: many-to-many references (list:reference) are not DB constraints,
               but pseudo-references implemented by the DAL. If you only want
               to find real foreign key constraints, then set m2m=False.
    """

    ftype = str(field.type)
    multiple = False
    if ftype[:9] == "reference":
        key = ftype[10:]
    elif m2m and ftype[:14] == "list:reference":
        key = ftype[15:]
        multiple = True
    else:
        key = current.s3db.virtual_reference(field)
        if not key:
            return (None, None, None)
    if "." in key:
        rtablename, key = key.split(".")
    else:
        rtablename = key
        rtable = current.s3db.table(rtablename)
        if rtable:
            key = rtable._id.name
        else:
            key = None
    return (rtablename, key, multiple)

# =============================================================================
def s3_flatlist(nested):
    """ Iterator to flatten mixed iterables of arbitrary depth """
    for item in nested:
        if isinstance(item, collections.Iterable) and \
           not isinstance(item, str):
            for sub in s3_flatlist(item):
                yield sub
        else:
            yield item

# =============================================================================
def s3_set_match_strings(matchDict, value):
    """
        Helper method for gis_search_ac and org_search_ac
        Find which field the search term matched & where

        @param matchDict: usually the record
        @param value: the search term
    """

    for key in matchDict:
        v = matchDict[key]
        if not isinstance(v, str):
            continue
        l = len(value)
        if v[:l].lower() == value:
            # Match needs to start from beginning
            matchDict["match_type"] = key
            matchDict["match_string"] = v[:l] # Maintain original case
            next_string = v[l:]
            if next_string:
                matchDict["next_string"] = next_string
            break
        elif key == "addr" and value in v.lower():
            # Match can start after the beginning (to allow for house number)
            matchDict["match_type"] = key
            pre_string, next_string = v.lower().split(value, 1)
            if pre_string:
                matchDict["pre_string"] = v[:len(pre_string)] # Maintain original case
            if next_string:
                matchDict["next_string"] = v[(len(pre_string) + l):] # Maintain original case
            matchDict["match_string"] = v[len(pre_string):][:l] # Maintain original case
            break

# =============================================================================
def s3_orderby_fields(table, orderby, expr=False):
    """
        Introspect and yield all fields involved in a DAL orderby
        expression.

        @param table: the Table
        @param orderby: the orderby expression
        @param expr: True to yield asc/desc expressions as they are,
                     False to yield only Fields
    """

    if not orderby:
        return

    adapter = S3DAL()
    COMMA = adapter.COMMA
    INVERT = adapter.INVERT

    if isinstance(orderby, str):
        items = orderby.split(",")
    elif type(orderby) is Expression:
        def expand(e):
            if isinstance(e, Field):
                return [e]
            if e.op == COMMA:
                return expand(e.first) + expand(e.second)
            elif e.op == INVERT:
                return [e] if expr else [e.first]
            return []
        items = expand(orderby)
    elif not isinstance(orderby, (list, tuple)):
        items = [orderby]
    else:
        items = orderby

    s3db = current.s3db
    tablename = table._tablename if table else None
    for item in items:
        if type(item) is Expression:
            if not isinstance(item.first, Field):
                continue
            f = item if expr else item.first
        elif isinstance(item, Field):
            f = item
        elif isinstance(item, str):
            fn, direction = (item.strip().split() + ["asc"])[:2]
            tn, fn = ([tablename] + fn.split(".", 1))[-2:]
            if tn:
                try:
                    f = s3db.table(tn, db_only=True)[fn]
                except (AttributeError, KeyError):
                    continue
            else:
                if current.response.s3.debug:
                    raise SyntaxError('Tablename prefix required for orderby="%s"' % item)
                else:
                    # Ignore
                    continue
            if expr and direction[:3] == "des":
                f = ~f
        else:
            continue
        yield f

# =============================================================================
def s3_get_extension(request=None):
    """
        Get the file extension in the path of the request

        @param request: the request object (web2py request or S3Request),
                        defaults to current.request
    """


    if request is None:
        request = current.request

    extension = request.extension
    if request.function == "ticket" and request.controller == "admin":
        extension = "html"
    elif "format" in request.get_vars:
        ext = request.get_vars.format
        if isinstance(ext, list):
            ext = ext[-1]
        extension = ext.lower() or extension
    else:
        ext = None
        for arg in request.args[::-1]:
            if "." in arg:
                ext = arg.rsplit(".", 1)[1].lower()
                break
        if ext:
            extension = ext
    return extension

# =============================================================================
def s3_get_extension_from_url(url):
    """
        Helper to read the format extension from a URL string

        @param url: the URL string

        @returns: the format extension as string, if any
    """

    ext = None
    if not url:
        return ext

    from urllib import parse as urlparse
    try:
        parsed = urlparse.urlparse(url)
    except (ValueError, AttributeError):
        pass
    else:
        if parsed.query:
            params = parsed.query.split(",")
            for param in params[::-1]:
                k, v = param.split("=") if "=" in param else None, None
                if k == "format":
                    ext = v.lower()
                    break
        if not ext:
            args = parsed.path.split("/")
            for arg in args[::-1]:
                if "." in arg:
                    ext = arg.rsplit(".", 1)[-1]
                    break

    return ext

# =============================================================================
def s3_set_extension(url, extension=None):
    """
        Add a file extension to the path of a url, replacing all
        other extensions in the path.

        @param url: the URL (as string)
        @param extension: the extension, defaults to the extension
                          of current. request
    """

    if extension == None:
        extension = s3_get_extension()
    #if extension == "html":
        #extension = ""

    u = urlparse.urlparse(url)

    path = u.path
    if path:
        if "." in path:
            elements = [p.split(".")[0] for p in path.split("/")]
        else:
            elements = path.split("/")
        if extension and elements[-1]:
            elements[-1] += ".%s" % extension
        path = "/".join(elements)
    return urlparse.urlunparse((u.scheme,
                                u.netloc,
                                path,
                                u.params,
                                u.query,
                                u.fragment))

# =============================================================================
class Traceback(object):
    """ Generate the traceback for viewing error Tickets """

    def __init__(self, text):
        """ Traceback constructor """

        self.text = text

    # -------------------------------------------------------------------------
    def xml(self):
        """ Returns the xml """

        output = self.make_links(CODE(self.text).xml())
        return output

    # -------------------------------------------------------------------------
    def make_link(self, path):
        """ Create a link from a path """

        tryFile = path.replace("\\", "/")

        if os.path.isabs(tryFile) and os.path.isfile(tryFile):
            folder, filename = os.path.split(tryFile)
            ext = os.path.splitext(filename)[1]
            app = current.request.args[0]

            editable = {"controllers": ".py", "models": ".py", "views": ".html"}
            l_ext = ext.lower()
            f_endswith = folder.endswith
            for key in editable.keys():
                check_extension = f_endswith("%s/%s" % (app, key))
                if l_ext == editable[key] and check_extension:
                    edit_url = URL(a = "admin",
                                   c = "default",
                                   f = "edit",
                                   args = [app, key, filename],
                                   )
                    return A('"' + tryFile + '"',
                             _href = edit_url,
                             _target = "_blank",
                             ).xml()
        return ""

    # -------------------------------------------------------------------------
    def make_links(self, traceback):
        """ Make links using the given traceback """

        lwords = traceback.split('"')

        # Make the short circuit compatible with <= python2.4
        result = lwords[0] if len(lwords) else ""

        i = 1

        while i < len(lwords):
            link = self.make_link(lwords[i])

            if link == "":
                result += '"' + lwords[i]
            else:
                result += s3_str(link)

                if i + 1 < len(lwords):
                    result += lwords[i + 1]
                    i = i + 1

            i = i + 1

        return result

# =============================================================================
def URL2(a=None, c=None, r=None):
    """
        Modified version of URL from gluon/html.py
            - used by views/layout_iframe.html for our jquery function

        @example:

        >>> URL(a="a",c="c")
        "/a/c"

        generates a url "/a/c" corresponding to application a & controller c
        If r=request is passed, a & c are set, respectively,
        to r.application, r.controller

        The more typical usage is:

        URL(r=request) that generates a base url with the present
        application and controller.

        The function (& optionally args/vars) are expected to be added
        via jquery based on attributes of the item.
    """
    application = controller = None
    if r:
        application = r.application
        controller = r.controller
    if a:
        application = a
    if c:
        controller = c
    if not (application and controller):
        raise SyntaxError("not enough information to build the url")
    #other = ""
    url = "/%s/%s" % (application, controller)
    return url

# =============================================================================
class S3CustomController(object):
    """
        Base class for custom controllers (template/controllers.py),
        implements common helper functions

        @ToDo: Add Helper Function for dataTables
        @ToDo: Add Helper Function for dataLists
    """

    @staticmethod
    def _view(template, filename):
        """
            Use a custom view template

            @param template: name of the template (determines the path)
            @param filename: name of the view template file
        """

        if "." in template:
            template = os.path.join(*(template.split(".")))

        view = os.path.join(current.request.folder, "modules", "templates",
                            template, "views", filename)

        try:
            # Pass view as file not str to work in compiled mode
            current.response.view = open(view, "rb")
        except IOError:
            msg = "Unable to open Custom View: %s" % view
            current.log.error("%s (%s)" % (msg, sys.exc_info()[1]))
            raise HTTP(404, msg)

# =============================================================================
class StringTemplateParser(object):
    """
        Helper to parse string templates with named keys

        @return: a list of keys (in order of appearance),
                 None for invalid string templates

        @example:
            keys = StringTemplateParser.keys("%(first_name)s %(last_name)s")
            # Returns: ["first_name", "last_name"]
    """
    def __init__(self):
        self._keys = []

    def __getitem__(self, key):
        self._keys.append(key)

    @classmethod
    def keys(cls, template):
        parser = cls()
        try:
            template % parser
        except TypeError:
            return None
        return parser._keys

# =============================================================================
class S3MarkupStripper(HTMLParser, object):
    """ Simple markup stripper """

    def __init__(self):
        super(S3MarkupStripper, self).__init__()
        #self.reset() # Included in super-init
        self.result = []

    def handle_data(self, d):
        self.result.append(d)

    def stripped(self):
        return "".join(self.result)

def s3_strip_markup(text):

    try:
        stripper = S3MarkupStripper()
        stripper.feed(text)
        text = stripper.stripped()
    except Exception:
        pass
    return text

# END =========================================================================
