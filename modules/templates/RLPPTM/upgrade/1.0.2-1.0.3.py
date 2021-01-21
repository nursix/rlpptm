# -*- coding: utf-8 -*-
#
# Database upgrade script
#
# RLPPTM Template Version 1.0.2 => 1.0.3
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/RLPPTM/upgrade/1.0.2-1.0.3.py
#
import datetime
import sys
#from s3 import S3DateTime

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
ptable = s3db.project_project
vtable = s3db.fin_voucher_program

IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "RLPPTM")

# -----------------------------------------------------------------------------
# Install projects
#
if not failed:
    info("Install projects")

    # Import new templates
    stylesheet = os.path.join(IMPORT_XSLT_FOLDER, "project", "project.xsl")
    filename = os.path.join(TEMPLATE_FOLDER, "project_project.csv")

    # Import, fail on any errors
    try:
        with open(filename, "r") as File:
            resource = s3db.resource("project_project")
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
# Link voucher programs to default project
#
if not failed:
    info("Link voucher programs to default project")

    query = (ptable.name == "COVID-19 Tests für Schulpersonal") & \
            (ptable.deleted == False)
    project = db(query).select(ptable.id, limitby=(0, 1)).first()
    if project:

        query = (vtable.project_id == None) & \
                (vtable.deleted == False)
        updated = db(query).update(project_id=project.id)
        infoln("...done (%s programs updated)" % updated)
    else:
        infoln("...failed (default project not found)")
        failed = True

# -----------------------------------------------------------------------------
# Install diseases
#
if not failed:
    info("Install diseases")

    # Import new templates
    stylesheet = os.path.join(IMPORT_XSLT_FOLDER, "disease", "disease.xsl")
    filename = os.path.join(TEMPLATE_FOLDER, "disease_disease.csv")

    # Import, fail on any errors
    try:
        with open(filename, "r") as File:
            resource = s3db.resource("disease_disease")
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
# Install processing types
#
if not failed:
    info("Deploy processing types for consent tracking")

    # Import new templates
    stylesheet = os.path.join(IMPORT_XSLT_FOLDER, "auth", "processing_type.xsl")
    filename = os.path.join(TEMPLATE_FOLDER, "auth_processing_type.csv")

    # Import, fail on any errors
    try:
        with open(filename, "r") as File:
            resource = s3db.resource("auth_processing_type")
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
