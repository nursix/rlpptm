# -*- coding: utf-8 -*-
#
# Database upgrade script
#
# RLPPTM Template Version 1.8.3 => 1.8.4
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/RLPPTM/upgrade/1.8.3-1.8.4.py
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
#ttable = s3db.org_organisation_type

IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "RLPPTM")

# -----------------------------------------------------------------------------
# Upgrade organisation types
#
if not failed:
    info("Upgrade Organisation Types")

    # Match existing by name
    s3db.configure("org_organisation_type",
                   deduplicate = S3Duplicate(),
                   )

    # Import new templates
    stylesheet = os.path.join(IMPORT_XSLT_FOLDER, "org", "organisation_type.xsl")
    filename = os.path.join(TEMPLATE_FOLDER, "org_organisation_type.csv")

    # Import, fail on any errors
    try:
        with open(filename, "r") as File:
            resource = s3db.resource("org_organisation_type")
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
# Finishing up
#
if failed:
    db.rollback()
    infoln("UPGRADE FAILED - Action rolled back.")
else:
    db.commit()
    infoln("UPGRADE SUCCESSFUL.")
