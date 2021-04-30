# -*- coding: utf-8 -*-
#
# Database upgrade script
#
# RLPPTM Template Version 1.8.1 => 1.8.2
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/RLPPTM/upgrade/1.8.1-1.8.2.py
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
ltable = s3db.org_service_site

IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "RLPPTM")

# -----------------------------------------------------------------------------
# Remove empty shipments
#
if not failed:
    info("Remove empty shipments")

    stable = s3db.inv_send
    titable = s3db.inv_track_item

    left = titable.on((titable.send_id == stable.id) & \
                      (titable.deleted == False))
    query = (stable.deleted == False) & \
            (titable.id == None)
    rows = db(query).select(stable.id,
                            groupby = stable.id,
                            left = left,
                            )
    empty = [row.id for row in rows]
    if empty:
        resource = s3db.resource("inv_send", id=empty)
        deleted = resource.delete(cascade = True)
        if resource.error:
            infoln("...failed (%s)" % resource.error)
            failed = True
        else:
            infoln("...done (%s shipments deleted)" % deleted)
    else:
        infoln("...skip (no empty shipments found)")

# -----------------------------------------------------------------------------
# Date all requests
#
if not failed:
    info("Date all requests")

    rtable = s3db.req_req
    query = (rtable.date == None) & \
            (rtable.deleted == False)
    updated = db(query).update(date = rtable.created_on,
                               modified_on = rtable.modified_on,
                               modified_by = rtable.modified_by,
                               )
    infoln("...done (%s records fixed)" % updated)

# -----------------------------------------------------------------------------
# Finishing up
#
if failed:
    db.rollback()
    infoln("UPGRADE FAILED - Action rolled back.")
else:
    db.commit()
    infoln("UPGRADE SUCCESSFUL.")
