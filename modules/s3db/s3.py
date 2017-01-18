# -*- coding: utf-8 -*-

""" S3 Framework Tables

    @copyright: 2009-2016 (c) Sahana Software Foundation
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

__all__ = ("S3HierarchyModel",
           "S3DashboardModel",
           "S3DynamicTablesModel",
           "s3_table_rheader",
           )

from gluon import *
from ..s3 import *

# =============================================================================
class S3HierarchyModel(S3Model):
    """ Model for stored object hierarchies """

    names = ("s3_hierarchy",
             )

    def model(self):

        # ---------------------------------------------------------------------
        # Stored Object Hierarchy
        #
        tablename = "s3_hierarchy"
        self.define_table(tablename,
                          Field("tablename", length=64),
                          Field("dirty", "boolean",
                                default = False,
                                ),
                          Field("hierarchy", "json"),
                          *s3_timestamp())

        # ---------------------------------------------------------------------
        # Return global names to s3.*
        #
        return {}

    # -------------------------------------------------------------------------
    def defaults(self):
        """ Safe defaults if module is disabled """

        return {}

# =============================================================================
class S3DashboardModel(S3Model):
    """ Model for stored dashboard configurations """

    names = ("s3_dashboard",
             )

    def model(self):

        define_table = self.define_table
        configure = self.configure

        # ---------------------------------------------------------------------
        # Stored Dashboard Configuration
        #
        tablename = "s3_dashboard"
        define_table(tablename,
                     Field("controller", length = 64,
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("function", length = 512,
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("version", length = 40,
                           readable = False,
                           writable = False,
                           ),
                     Field("next_id", "integer",
                           readable = False,
                           writable = False,
                           ),
                     Field("layout",
                           default = S3DashboardConfig.DEFAULT_LAYOUT,
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("title",
                           ),
                     Field("widgets", "json",
                           requires = IS_JSONS3(),
                           ),
                     Field("active", "boolean",
                           default = True,
                           ),
                     *s3_meta_fields())

        configure(tablename,
                  onaccept = self.dashboard_onaccept,
                  )

        # ---------------------------------------------------------------------
        # Link Dashboard Config <=> Person Entity
        #
        # @todo

        # ---------------------------------------------------------------------
        # Return global names to s3.*
        #
        return {}

    # -------------------------------------------------------------------------
    def defaults(self):
        """ Safe defaults if module is disabled """

        return {}

    # -------------------------------------------------------------------------
    @staticmethod
    def dashboard_onaccept(form):
        """
            On-accept routine for dashboard configurations
                - make sure there is at most one active config for the same
                  controller/function
        """

        db = current.db

        try:
            record_id = form.vars.id
        except AttributeError:
            return

        table = current.s3db.s3_dashboard
        query = table.id == record_id

        row = db(query).select(table.id,
                               table.controller,
                               table.function,
                               table.active,
                               limitby = (0, 1),
                               ).first()
        if not row:
            return

        if row.active:
            # Deactivate all other configs for the same controller/function
            query = (table.controller == row.controller) & \
                    (table.function == row.function) & \
                    (table.id != row.id) & \
                    (table.active == True) & \
                    (table.deleted != True)
            db(query).update(active = False)

# =============================================================================
class S3DynamicTablesModel(S3Model):
    """ Model for dynamic tables """

    names = ("s3_table",
             "s3_field",
             )

    def model(self):

        T = current.T

        db = current.db
        s3 = current.response.s3

        define_table = self.define_table
        crud_strings = s3.crud_strings

        # ---------------------------------------------------------------------
        # Dynamic Table
        #
        tablename = "s3_table"
        define_table(tablename,
                     Field("name", length=128, unique=True, notnull=True,
                           label = T("Table Name"),
                           requires = [IS_NOT_EMPTY(),
                                       IS_LENGTH(128),
                                       IS_NOT_IN_DB(db, "s3_table.name"),
                                       ],
                           ),
                     #s3_comments(),
                     *s3_meta_fields())

        # Components
        self.add_components(tablename,
                            s3_field = "table_id",
                            )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Table"),
            title_display = T("Table Details"),
            title_list = T("Tables"),
            title_update = T("Edit Table"),
            label_list_button = T("List Tables"),
            label_delete_button = T("Delete Table"),
            msg_record_created = T("Table created"),
            msg_record_modified = T("Table updated"),
            msg_record_deleted = T("Table deleted"),
            msg_list_empty = T("No Tables currently defined"),
        )

        # Reusable field
        represent = S3Represent(lookup=tablename, show_link=True)
        table_id = S3ReusableField("table_id", "reference %s" % tablename,
                                   label = T("Table"),
                                   represent = represent,
                                   requires = IS_ONE_OF(db, "%s.id" % tablename,
                                                        represent,
                                                        ),
                                   sortby = "name",
                                   )

        # ---------------------------------------------------------------------
        # Field in Dynamic Table
        #
        tablename = "s3_field"
        define_table(tablename,
                     table_id(notnull = True,
                              ondelete = "CASCADE",
                              ),
                     Field("name", length=128, notnull=True,
                           label = T("Field Name"),
                           requires = [IS_NOT_EMPTY(),
                                       IS_LENGTH(128),
                                       ],
                           ),
                     Field("field_type", length=128, notnull=True,
                           default = "string",
                           label = T("Field Type"),
                           requires = [IS_NOT_EMPTY(),
                                       IS_LENGTH(128),
                                       ],
                           ),
                     Field("label",
                           label = T("Label"),
                           ),
                     #s3_comments(),
                     *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Field"),
            title_display = T("Field Details"),
            title_list = T("Fields"),
            title_update = T("Edit Field"),
            label_list_button = T("List Fields"),
            label_delete_button = T("Delete Field"),
            msg_record_created = T("Field created"),
            msg_record_modified = T("Field updated"),
            msg_record_deleted = T("Field deleted"),
            msg_list_empty = T("No Fields currently defined"),
        )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

# =============================================================================
def s3_table_rheader(r, tabs=None):

    if r.representation != "html":
        # Resource headers only used in interactive views
        return None

    record = r.record
    resource = r.resource

    rheader = None

    if record:

        T = current.T
        rheader_fields = []

        if r.tablename == "s3_table":

            if not tabs:
                tabs = [(T("Table"), None),
                        (T("Fields"), "field"),
                        ]

            rheader_fields = [["name"],
                              ]

        rheader = S3ResourceHeader(rheader_fields, tabs)(r,
                                                         table = resource.table,
                                                         record = record,
                                                         )

    return rheader

# END =========================================================================
