# -*- coding: utf-8 -*-
#
# Database upgrade script
#
# RLPPTM Template Version 1.6.0 => 1.6.1
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/RLPPTM/upgrade/1.6.0-1.6.1.py
#
import sys

#from gluon.storage import Storage
#from gluon.tools import callback

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
mtable = s3db.org_group_membership

IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "RLPPTM")

# -----------------------------------------------------------------------------
# Add Missing OrgGroup Affiliations
#
if not failed:
    info("Add Missing OrgGroup Affiliations")

    # Get all memberships
    query = (mtable.deleted == False)
    rows = db(query).select(mtable.id,
                            mtable.organisation_id,
                            mtable.group_id,
                            mtable.deleted,
                            mtable.deleted_fk,
                            )

    # Update affiliations
    checked = 0
    org_update_affiliations = s3db.org_update_affiliations
    for row in rows:
        info(".")
        org_update_affiliations("org_group_membership", row)
        checked += 1

    infoln("...done (%s records checked)" % checked)

# -----------------------------------------------------------------------------
# Finishing up
#
if failed:
    db.rollback()
    infoln("UPGRADE FAILED - Action rolled back.")
else:
    db.commit()
    infoln("UPGRADE SUCCESSFUL.")
