# -*- coding: utf-8 -*-
#
# Database upgrade script
#
# RLPPTM Template Version 1.15.0 => 1.16.0
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/RLPPTM/upgrade/1.15.0-1.16.0.py
#
import sys

#from gluon.storage import Storage
#from gluon.tools import callback
#from core import S3Duplicate

# Override auth (disables all permission checks)
auth.override = True

# Failed-flag
failed = False

# Info
def info(msg):
    sys.stderr.write("%s" % msg)
def infoln(msg):
    sys.stderr.write("%s\n" % msg)

# Load models for tables
#ftable = s3db.org_facility

IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "RLPPTM")

# -----------------------------------------------------------------------------
# Upgrade user roles
#
if not failed:
    info("Upgrade user roles")

    bi = s3base.S3BulkImporter()
    filename = os.path.join(TEMPLATE_FOLDER, "auth_roles.csv")

    with open(filename, "r") as File:
        try:
            bi.import_role(filename)
        except Exception as e:
            infoln("...failed")
            infoln(sys.exc_info()[1])
            failed = True
        else:
            infoln("...done")

# -----------------------------------------------------------------------------
# Assign NEWSLETTER_AUTHOR role to all ORG_GROUP_ADMINs
#
if not failed:
    info("Assign newsletter author role")

    utable = auth.table_user()
    gtable = auth.table_group()
    mtable = auth.table_membership()

    join = [mtable.on((mtable.user_id == utable.id) & \
                      (mtable.deleted == False)),
            gtable.on((gtable.id == mtable.group_id) & \
                      (gtable.uuid == "ORG_GROUP_ADMIN")),
            ]
    query = ((utable.registration_key == None) | (utable.registration_key == "")) & \
            (utable.deleted == False)
    rows = db(query).select(utable.id, mtable.pe_id, join=join)
    updated = 0
    info("...")
    for row in rows:
        user = row.auth_user
        membership = row.auth_membership
        auth.s3_assign_role(user.id, "NEWSLETTER_AUTHOR", for_pe=membership.pe_id)
        info(".")
        updated += 1

    infoln("...done (%s users assigned)" % updated)

# -----------------------------------------------------------------------------
# Fix realm entities of saved filters
#
if not failed:
    info("Fix realm of saved filters")

    table = s3db.pr_filter
    auth.set_realm_entity(table, table.id>0, force_update=True)
    infoln("...done")

# -----------------------------------------------------------------------------
# Country name update
#
if not failed:
    info("Update MK country name")

    table = s3db.gis_location
    query = (table.uuid == "urn:iso:std:iso:3166:-1:code:MK") & \
            (table.level == "L0")

    name = "North Macedonia"
    updated = db(query).update(name=name, L0=name)

    infoln("...done (%s records updated)" % updated)

# -----------------------------------------------------------------------------
# Finishing up
#
if failed:
    db.rollback()
    infoln("UPGRADE FAILED - Action rolled back.")
else:
    db.commit()
    infoln("UPGRADE SUCCESSFUL.")
