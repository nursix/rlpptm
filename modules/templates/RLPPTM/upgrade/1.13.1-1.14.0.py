# -*- coding: utf-8 -*-
#
# Database upgrade script
#
# RLPPTM Template Version 1.13.1 => 1.14.0
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/RLPPTM/upgrade/1.13.1-1.14.0.py
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
ftable = s3db.org_facility

IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "RLPPTM")

# -----------------------------------------------------------------------------
# Update facility obsolete-statuses
#
if not failed:
    info("Update facility obsolete-statuses")

    query = (ftable.obsolete == True) & \
            (ftable.deleted == False)
    rows = db(query).select(ftable.id,
                            ftable.site_id,
                            )
    updated = 0
    for row in rows:
        s3db.update_super(ftable, row)
        updated += 1
        info(".")

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
