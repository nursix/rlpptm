# -*- coding: utf-8 -*-

"""
    Custom rheaders for RLPPTM template

    @license: MIT
"""

from gluon import current

from s3 import S3ResourceHeader, s3_rheader_resource

# =============================================================================
def rlpptm_fin_rheader(r, tabs=None):
    """ FIN custom resource headers """

    if r.representation != "html":
        # Resource headers only used in interactive views
        return None

    tablename, record = s3_rheader_resource(r)
    if tablename != r.tablename:
        resource = current.s3db.resource(tablename, id=record.id)
    else:
        resource = r.resource

    rheader = None
    rheader_fields = []
    rheader_title = None
    img = None

    if record:
        T = current.T

        if tablename == "fin_voucher":

            if not tabs:

                tabs = [(T("Voucher"), None),
                        ]

            rheader_title = None
            rheader_fields = [["program_id",
                               ],
                              ["signature",
                               ],
                              ["date",
                               ],
                              ["valid_until",
                               ],
                              ]

            signature = record.signature
            if signature:
                try:
                    import qrcode
                except ImportError:
                    pass
                else:
                    from s3 import s3_qrcode_represent
                    img = s3_qrcode_represent(signature, show_value=False)
                    img.add_class("rheader-qrcode")

        rheader = S3ResourceHeader(rheader_fields, tabs, title=rheader_title)
        rheader = rheader(r, table = resource.table, record = record)

        if img:
            rheader.insert(0, img)

    return rheader

# =============================================================================
def rlpptm_org_rheader(r, tabs=None):
    """ ORG custom resource headers """

    if r.representation != "html":
        # Resource headers only used in interactive views
        return None

    tablename, record = s3_rheader_resource(r)
    if tablename != r.tablename:
        resource = current.s3db.resource(tablename, id=record.id)
    else:
        resource = r.resource

    rheader = None
    rheader_fields = []

    if record:
        T = current.T

        if tablename == "org_organisation":

            auth = current.auth
            is_org_group_admin = auth.s3_has_role("ORG_GROUP_ADMIN")

            if not tabs:

                invite_tab = None
                sites_tab = None

                db = current.db
                s3db = current.s3db
                gtable = s3db.org_group
                mtable = s3db.org_group_membership
                query = (mtable.organisation_id == record.id) & \
                        (mtable.group_id == gtable.id)
                group = db(query).select(gtable.name,
                                         limitby = (0, 1)
                                         ).first()
                if group:
                    from .config import TESTSTATIONS, SCHOOLS
                    if group.name == TESTSTATIONS:
                        sites_tab = (T("Test Stations"), "facility")
                    elif group.name == SCHOOLS:
                        sites_tab = (T("Administrative Offices"), "office")
                        if is_org_group_admin:
                            invite_tab = (T("Invite"), "invite")

                tabs = [(T("Organisation"), None),
                        invite_tab,
                        sites_tab,
                        (T("Staff"), "human_resource"),
                        ]

            # Check for active user accounts:
            if is_org_group_admin:

                from .helpers import get_org_accounts
                active = get_org_accounts(record.id)[0]

                active_accounts = lambda row: len(active)
                rheader_fields = [[(T("Active Accounts"), active_accounts)],
                                  ]
            else:
                rheader_fields = []

            rheader_title = "name"

        rheader = S3ResourceHeader(rheader_fields, tabs, title=rheader_title)
        rheader = rheader(r, table = resource.table, record = record)

    return rheader

# =============================================================================
def rlpptm_profile_rheader(r, tabs=None):
    """ Custom rheader for default/person """

    if r.representation != "html":
        # Resource headers only used in interactive views
        return None

    tablename, record = s3_rheader_resource(r)
    if tablename != r.tablename:
        resource = current.s3db.resource(tablename, id=record.id)
    else:
        resource = r.resource

    rheader = None
    rheader_fields = []

    if record:

        T = current.T

        if tablename == "pr_person":

            tabs = [(T("Person Details"), None),
                    (T("User Account"), "user_profile"),
                    (T("Contact Information"), "contacts"),
                    ]
            rheader_fields = []

        rheader = S3ResourceHeader(rheader_fields, tabs)(r,
                                                         table = resource.table,
                                                         record = record,
                                                         )
    return rheader

# END =========================================================================
