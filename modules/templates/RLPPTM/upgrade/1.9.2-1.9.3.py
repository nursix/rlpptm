# -*- coding: utf-8 -*-
#
# Database upgrade script
#
# RLPPTM Template Version 1.9.2 => 1.9.3
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/RLPPTM/upgrade/1.9.2-1.9.3.py
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
rtable = s3db.disease_testing_report

IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "RLPPTM")

# -----------------------------------------------------------------------------
# Fix ownership for daily reports
#
if not failed:
    info("Fix ownership of daily reports")

    query = (rtable.deleted == False)
    rows = db(query).select()

    set_record_owner = auth.s3_set_record_owner
    updated = 0
    for row in rows:
        set_record_owner(table, row, force_update=True)
        info(".")
        updated += 1

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
