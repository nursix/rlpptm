# -*- coding: utf-8 -*-
#
# Database upgrade script
#
# RLPPTM Template Version 1.12.2 => 1.12.3
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/RLPPTM/upgrade/1.12.2-1.12.3.py
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
ptable = s3db.pr_person
htable = s3db.hrm_human_resource

IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "RLPPTM")

# -----------------------------------------------------------------------------
# Update realms for person records
#
if not failed:
    info("Update realms for person records")

    # Configure components to inherit realm_entity from person
    s3db.configure("pr_person",
                   realm_components = ("person_details",
                                       "contact",
                                       "address",
                                       ),
                   )

    # Update realm
    auth.set_realm_entity(ptable, ptable.id>0, force_update=True)

    infoln("...done")

# -----------------------------------------------------------------------------
# Update realms for HR records
#
if not failed:
    info("Update realms for HR records")

    # Update realm
    auth.set_realm_entity(htable, htable.id>0, force_update=True)

    infoln("...done")

# -----------------------------------------------------------------------------
# Deploy job titles
#
if not failed:
    info("Deploy job titles")

    # File and Stylesheet Paths
    stylesheet = os.path.join(IMPORT_XSLT_FOLDER, "hrm", "job_title.xsl")
    filename = os.path.join(TEMPLATE_FOLDER, "hrm_job_title.csv")

    # Import, fail on any errors
    try:
        with open(filename, "r") as File:
            resource = s3db.resource("hrm_job_title")
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
# Finishing up
#
if failed:
    db.rollback()
    infoln("UPGRADE FAILED - Action rolled back.")
else:
    db.commit()
    infoln("UPGRADE SUCCESSFUL.")
