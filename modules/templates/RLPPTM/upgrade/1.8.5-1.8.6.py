# -*- coding: utf-8 -*-
#
# Database upgrade script
#
# RLPPTM Template Version 1.8.5 => 1.8.6
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/RLPPTM/upgrade/1.8.5-1.8.6.py
#
import sys

#from gluon.storage import Storage
#from gluon.tools import callback

from s3 import S3Duplicate

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
dtable = s3db.org_site_details
smtable = s3db.org_service_mode

IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "RLPPTM")

# -----------------------------------------------------------------------------
# Install booking modes
#
if not failed:
    info("Install booking modes")

    # Import new templates
    stylesheet = os.path.join(IMPORT_XSLT_FOLDER, "org", "booking_mode.xsl")
    filename = os.path.join(TEMPLATE_FOLDER, "org_booking_mode.csv")

    # Import, fail on any errors
    try:
        with open(filename, "r") as File:
            resource = s3db.resource("org_booking_mode")
            resource.import_xml(File, format="csv", stylesheet=stylesheet)
    except:
        infoln("...failed")
        infoln(sys.exc_info()[1])
        failed = True
    else:
        if resource.error:
            infoln("...failed")
            infoln(resource.error)
            failed = True
        else:
            infoln("...done")

# -----------------------------------------------------------------------------
# Install service modes
#
if not failed:
    info("Install service modes")

    # Import new templates
    stylesheet = os.path.join(IMPORT_XSLT_FOLDER, "org", "service_mode.xsl")
    filename = os.path.join(TEMPLATE_FOLDER, "org_service_mode.csv")

    # Import, fail on any errors
    try:
        with open(filename, "r") as File:
            resource = s3db.resource("org_service_mode")
            resource.import_xml(File, format="csv", stylesheet=stylesheet)
    except:
        infoln("...failed")
        infoln(sys.exc_info()[1])
        failed = True
    else:
        if resource.error:
            infoln("...failed")
            infoln(resource.error)
            failed = True
        else:
            infoln("...done")

# -----------------------------------------------------------------------------
# Install site details for all facilities
#
if not failed:
    info("Upgrade facilities")

    # Look up default service mode
    query = (smtable.name == "stationär") & \
            (smtable.deleted == False)
    row = db(query).select(smtable.id,
                           limitby = (0, 1),
                           ).first()
    default_service_mode = row.id if row else None

    # Look up facilities which have no site_details yet
    left = dtable.on((dtable.site_id == ftable.site_id) & \
                     (dtable.deleted == False))
    query = (ftable.deleted == False) & \
            (dtable.id == None)
    rows = db(query).select(ftable.site_id,
                            left = left,
                            )
    added = 0
    for row in rows:
        info(".")
        details = {"site_id": row.site_id,
                   "service_mode_id": default_service_mode,
                   }
        try:
            record_id = dtable.insert(**details)
        except:
            record_id = None
        if record_id:
            added += 1
        else:
            failed = True
            infoln("...failed")
    if not failed:
        infoln("...done (%s records added)" % added)

# -----------------------------------------------------------------------------
# Finishing up
#
if failed:
    db.rollback()
    infoln("UPGRADE FAILED - Action rolled back.")
else:
    db.commit()
    infoln("UPGRADE SUCCESSFUL.")
