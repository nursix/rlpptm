# -*- coding: utf-8 -*-
#
# Database upgrade script
#
# RLPPTM Template Version 1.9.1 => 1.9.2
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/RLPPTM/upgrade/1.9.1-1.9.2.py
#
import sys

#from gluon.storage import Storage
#from gluon.tools import callback
#from s3 import S3Duplicate

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
ptable = s3db.project_project
ltable = s3db.project_organisation
otable = s3db.org_organisation

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
# Assign TEST_PROVIDER role
#
if not failed:
    info("Assign TEST_PROVIDER role")

    from templates.RLPPTM.config import LSJV
    from templates.RLPPTM.helpers import get_role_users

    assign_role = current.auth.s3_assign_role

    # Get all organisations that are partners in the TESTS-PUBLIC project
    join = [ltable.on((ltable.organisation_id == otable.id) & \
                      (ltable.deleted == False)),
            ptable.on((ptable.id == ltable.project_id) & \
                      (ptable.code == "TESTS-PUBLIC")),
            ]
    query = (otable.name != LSJV) & (otable.deleted == False)
    rows = db(query).select(otable.id, otable.pe_id, join=join)

    # For each of those organisation, find the OrgAdmins and
    # assign them the TEST_PROVIDER role
    for row in rows:
        org_pe_id = row.pe_id
        users = get_role_users("ORG_ADMIN", pe_id=org_pe_id)
        if not users:
            continue
        for user_id in users:
            assign_role(user_id, "TEST_PROVIDER", for_pe=org_pe_id)
            info(".")

    infoln("...done")

# -----------------------------------------------------------------------------
# Finishing up
#
if failed:
    db.rollback()
    infoln("UPGRADE FAILED - Action rolled back.")
else:
    db.commit()
    infoln("UPGRADE SUCCESSFUL.")
