# -*- coding: utf-8 -*-

from os import path

from gluon import *
from gluon.storage import Storage

from s3 import S3CustomController

THEME = "RMSAmericas"

# =============================================================================
class index(S3CustomController):
    """ Custom Home Page """

    def __call__(self):

        output = {}

        # Allow editing of page content from browser using CMS module
        if current.deployment_settings.has_module("cms"):
            system_roles = current.auth.get_system_roles()
            ADMIN = system_roles.ADMIN in current.session.s3.roles
            s3db = current.s3db
            table = s3db.cms_post
            ltable = s3db.cms_post_module
            module = "default"
            resource = "index"
            query = (ltable.module == module) & \
                    ((ltable.resource == None) | \
                     (ltable.resource == resource)) & \
                    (ltable.post_id == table.id) & \
                    (table.deleted != True)
            item = current.db(query).select(table.body,
                                            table.id,
                                            limitby=(0, 1)).first()
            if item:
                if ADMIN:
                    item = DIV(XML(item.body),
                               BR(),
                               A(current.T("Edit"),
                                 _href=URL(c="cms", f="post",
                                           args=[item.id, "update"]),
                                 _class="action-btn"))
                else:
                    item = DIV(XML(item.body))
            elif ADMIN:
                if current.response.s3.crud.formstyle == "bootstrap":
                    _class = "btn"
                else:
                    _class = "action-btn"
                item = A(current.T("Edit"),
                         _href=URL(c="cms", f="post", args="create",
                                   vars={"module": module,
                                         "resource": resource
                                         }),
                         _class="%s cms-edit" % _class)
            else:
                item = ""
        else:
            item = ""
        output["item"] = item

        self._view(THEME, "index.html")
        return output

# =============================================================================
class apps(S3CustomController):
    """ App Switcher """

    def __call__(self):

        T = current.T
        auth = current.auth
        has_roles = auth.s3_has_roles
        ORG_ADMIN = current.session.s3.system_roles.ORG_ADMIN

        # Which apps are available for this user?
        apps = []
        apps_append = apps.append
        _div = self.div

        if has_roles((ORG_ADMIN,
                      "hr_manager",
                      "hr_assistant",
                      "training_coordinator",
                      "training_assistant",
                      "surge_capacity_manager",
                      "disaster_manager",
                      )):
            apps_append(_div(label = T("Human Talent"),
                             url = URL(c = "hrm",
                                       f = "index",
                                       ),
                             image = "human_talent.png",
                             _class = "alh",
                             ))

        if has_roles((ORG_ADMIN,
                      "training_coordinator",
                      "training_assistant",
                      "ns_training_manager",
                      "ns_training_assistant",
                      "surge_capacity_manager",
                      "disaster_manager",
                      )):
            apps_append(_div(label = T("Training"),
                             url = URL(c = "hrm",
                                       f = "training_event",
                                       ),
                             image = "training.png",
                             ))

        if auth.permission.accessible_url(c = "member",
                                          f = "membership",
                                          ):
            apps_append(_div(label = T("Partners"),
                             url = URL(c = "member",
                                       f = "membership",
                                       ),
                             image = "partners.png",
                             ))

        if has_roles((ORG_ADMIN,
                      "wh_manager",
                      "national_wh_manager",
                      )):
            apps_append(_div(label = T("Warehouses"),
                             url = URL(c = "inv",
                                       f = "index",
                                       ),
                             image = "warehouses.png",
                             _class = "alw",
                             ))

        if has_roles(("project_reader",
                      "project_manager",
                      "monitoring_evaluation",
                      )):
            apps_append(_div(label = T("Projects"),
                             url = URL(c = "project",
                                       f = "project",
                                       args = "summary",
                                       ),
                             image = "projects.png",
                             ))

        if has_roles(("surge_capacity_manager",
                      "disaster_manager",
                      )):
            apps_append(_div(label = T("RIT"),
                             url = URL(c = "deploy",
                                       f = "mission",
                                       args = "summary",
                                       vars = {"status__belongs": 2},
                                       ),
                             image = "RIT.png",
                             ))

        # Layout the apps
        len_apps = len(apps)
        if len_apps == 0:
            # No Apps available
            # This generally gets caught earlier & user sees no App Switcher at all
            resize = True
            height = 112
            width = 110
            apps = DIV(_class = "row",
                       )
        elif len_apps == 1:
            # 1x1
            resize = True
            height = 112
            width = 110
            apps[0]["_class"] = "small-12 columns"
            apps = DIV(apps[0],
                       _class = "row",
                       )
        elif len_apps == 2:
            # 1x2
            resize = True
            height = 112
            width = 220
            apps[0]["_class"] = "small-6 columns"
            apps[1]["_class"] = "small-6 columns"
            apps = DIV(apps[0],
                       apps[1],
                       _class = "row",
                       )
        elif len_apps == 3:
            # 2x2
            resize = True
            height = 224
            width = 220
            apps[0]["_class"] = "small-6 columns"
            apps[1]["_class"] = "small-6 columns"
            apps[2]["_class"] = "small-6 columns"
            apps = TAG[""](DIV(apps[0],
                               apps[1],
                               _class = "row",
                               ),
                           DIV(apps[2],
                               _class = "row",
                               ),
                           )
        elif len_apps == 4:
            # 2x2
            resize = True
            height = 224
            width = 220
            apps[0]["_class"] = "small-6 columns"
            apps[1]["_class"] = "small-6 columns"
            apps[2]["_class"] = "small-6 columns"
            apps[3]["_class"] = "small-6 columns"
            apps = TAG[""](DIV(apps[0],
                               apps[1],
                               _class = "row",
                               ),
                           DIV(apps[2],
                               apps[3],
                               _class = "row",
                               ),
                           )
        else:
            # 2xX
            resize = False
            row2 = DIV(apps[3],
                       apps[4],
                       _class = "row",
                       )
            if len_apps == 6:
                row2.append(apps[5])
            apps = TAG[""](DIV(apps[0],
                               apps[1],
                               apps[2],
                               _class = "row",
                               ),
                           row2,
                           )

        output = {"apps": apps,
                  }

        if resize:
            # Insert JS to resize the parent iframe
            output["js"] = '''window.parent.$('#apps-frame').parent().height(%s).width(%s)''' % \
                                (height, width)

        self._view(THEME, "apps.html")
        return output

    # -------------------------------------------------------------------------
    @staticmethod
    def div(label,
            url,
            image,
            _class = None
            ):

        if _class:
            #Extra class on label's span to fit it in better
            _class = "al %s" % _class
        else:
            _class = "al"

        div = DIV(DIV(A(IMG(_src = URL(c="static", f="themes",
                                       args = [THEME,
                                               "img",
                                               image,
                                               ]),
                            _class = "ai",
                            _height = "64",
                            _width = "64",
                            ),
                        SPAN(label,
                             _class = _class,
                             ),
                        _href = url,
                        _target = "_top",
                        ),
                      _class = "ah",
                      ),
                  _class = "small-4 columns",
                  )

        return div

# =============================================================================
def deploy_index():
    """
        Custom module homepage for deploy (=RIT) to display online
        documentation for the module
    """

    response = current.response

    def prep(r):
        default_url = URL(f="mission", args="summary", vars={})
        return current.s3db.cms_documentation(r, "RIT", default_url)
    response.s3.prep = prep
    output = current.rest_controller("cms", "post")

    # Custom view
    view = path.join(current.request.folder,
                     "modules",
                     "templates",
                     THEME,
                     "views",
                     "deploy",
                     "index.html",
                     )
    try:
        # Pass view as file not str to work in compiled mode
        response.view = open(view, "rb")
    except IOError:
        from gluon.http import HTTP
        raise HTTP(404, "Unable to open Custom View: %s" % view)

    return output

# END =========================================================================
