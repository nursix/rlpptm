# -*- coding: utf-8 -*-
#
# Database upgrade script
#
# RLPPTM Template Version 1.7.2 => 1.8.0
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/RLPPTM/upgrade/1.7.2-1.8.0.py
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
# Install warehouse types
#
if not failed:
    info("Install Warehouse Types")

    # Import new templates
    stylesheet = os.path.join(IMPORT_XSLT_FOLDER, "inv", "warehouse_type.xsl")
    filename = os.path.join(TEMPLATE_FOLDER, "inv_warehouse_type.csv")

    # Import, fail on any errors
    try:
        with open(filename, "r") as File:
            resource = s3db.resource("inv_warehouse_type")
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
# Upgrade realms for send/recv
#
if not failed:
    info("Upgrade realms for shipments and deliveries")

    stable = s3db.inv_send
    query = (stable.deleted == False)
    auth.set_realm_entity(stable, query, force_update=True)

    rtable = s3db.inv_recv
    query = (rtable.deleted == False)
    auth.set_realm_entity(rtable, query, force_update=True)

    infoln("...done")

# -----------------------------------------------------------------------------
# Upgrade user roles
#
if not failed:
    info("Upgrade user roles")

    auth.permission.delete_acl("SUPPLY_COORDINATOR", c="inv", f="send")
    auth.permission.delete_acl("SUPPLY_COORDINATOR", c="inv", f="send", entity="any")

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
