# -*- coding: utf-8 -*-
#
# Database upgrade script
#
# RLPPTM Template Version 1.5.3 => 1.5.4
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/RLPPTM/upgrade/1.5.3-1.5.4.py
#
#import datetime
import sys
import uuid
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
# Add OrgID-tag for all organisations
#
if not failed:
    info("Install OrgID-Tags")

    # Get all organisations which do not have a tag yet
    left = ttable.on((ttable.organisation_id == otable.id) & \
                     (ttable.tag == "OrgID") & \
                     (ttable.deleted == False))

    query = (otable.deleted == False) & \
            (ttable.id == None)
    organisations = db(query).select(otable.id,
                                     otable.uuid,
                                     left = left,
                                     )

    added = 0
    for organisation in organisations:

        try:
            uid = int(organisation.uuid[9:14], 16)
        except (TypeError, ValueError):
            uid = int(uuid.uuid4().urn[9:14], 16)

        value = "%06d%04d" % (uid, organisation.id)
        ttable.insert(organisation_id = organisation.id,
                      tag = "OrgID",
                      value = value,
                      )
        added += 1

    infoln("...done (%s tags added)" % added)

# -----------------------------------------------------------------------------
# Finishing up
#
if failed:
    db.rollback()
    infoln("UPGRADE FAILED - Action rolled back.")
else:
    db.commit()
    infoln("UPGRADE SUCCESSFUL.")
