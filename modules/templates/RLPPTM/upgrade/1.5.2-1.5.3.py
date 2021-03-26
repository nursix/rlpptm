# -*- coding: utf-8 -*-
#
# Database upgrade script
#
# RLPPTM Template Version 1.5.2 => 1.5.3
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/RLPPTM/upgrade/1.5.2-1.5.3.py
#
#import datetime
import sys
from s3 import S3Duplicate

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
otable = s3db.org_organisation
ttable = s3db.org_organisation_tag

gtable = auth.settings.table_group
mtable = auth.settings.table_membership
ltable = s3db.pr_person_user

IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "RLPPTM")

# -----------------------------------------------------------------------------
# Add Requester-tag for all organisations
#
if not failed:
    info("Install Requester-Tags")

    # Get all users with the SUPPLY_REQUESTER role
    join = gtable.on((gtable.id == mtable.group_id) & \
                     (gtable.uuid == "SUPPLY_REQUESTER") & \
                     (gtable.deleted == False)
                     )
    left = ltable.on((ltable.user_id == mtable.user_id) & \
                     (ltable.deleted == False)
                     )
    query = ((mtable.pe_id == None) | (mtable.pe_id != 0)) & \
            (mtable.deleted == False)
    rows = db(query).select(mtable.user_id,
                            mtable.pe_id,
                            ltable.pe_id,
                            join = join,
                            left = left,
                            )
    has_requesters = {}
    for row in rows:
        realm = row[mtable.pe_id]
        if realm:
            has_requesters[realm] = True
            continue
        # Get the default realm of the user
        user_pe_id = row[ltable.pe_id]
        if user_pe_id:
            realms = s3db.pr_realm(user_pe_id)
            for realm in realms:
                has_requesters[realm] = True

    # Get all organisations which do not have a tag yet
    left = ttable.on((ttable.organisation_id == otable.id) & \
                     (ttable.tag == "REQUESTER") & \
                     (ttable.deleted == False))

    query = (otable.deleted == False) & \
            (ttable.id == None)
    organisations = db(query).select(otable.id,
                                     otable.pe_id,
                                     left = left,
                                     )

    added = 0
    for organisation in organisations:

        value = "Y" if has_requesters.get(organisation.pe_id) else "N"
        ttable.insert(organisation_id = organisation.id,
                      tag = "REQUESTER",
                      value = value,
                      )
        added += 1

    infoln("...done (%s tags added)" % added)

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
# Drop SUPPLY_REQUESTER role
#
if not failed:
    info("Drop SUPPLY_REQUESTER role")

    auth.s3_delete_role("SUPPLY_REQUESTER")
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
