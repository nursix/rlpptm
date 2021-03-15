# -*- coding: utf-8 -*-
#
# Database upgrade script
#
# RLPPTM Template Version 1.4.1 => 1.4.2
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/RLPPTM/upgrade/1.4.1-1.4.2.py
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
ctable = s3db.supply_catalog
wtable = s3db.inv_warehouse
otable = s3db.org_organisation

IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "RLPPTM")

# -----------------------------------------------------------------------------
# Deploy supply catalog if it doesn't exist
#
if not failed:
    info("Deploy default supply item catalog")

    query = (ctable.id > 0)
    row = db(query).select(ctable.id, limitby=(0, 1)).first()
    if not row:
        catalog_id = ctable.insert(name = settings.get_supply_catalog_default())
        if catalog_id:
            infoln("...done")
        else:
            infoln("...failed")
            failed = True
    else:
        infoln("...catalog exists, skip")

# -----------------------------------------------------------------------------
# Deploy warehouse for LSJV if it doesn't exist
#
if not failed:
    info("Deploy default warehouse for LSJV")

    from templates.RLPPTM.config import LSJV

    left = wtable.on((wtable.organisation_id == otable.id) & \
                     (wtable.deleted == False))
    query = (otable.name == LSJV) & \
            (otable.deleted == False)

    row = db(query).select(otable.id,
                           wtable.id,
                           left = left,
                           limitby = (0, 1),
                           ).first()
    if row:
        wh = row.inv_warehouse
        if not wh.id:
            whid = wtable.insert(name = "LSJV Zentrallager",
                                 organisation_id = row.org_organisation.id,
                                 )
            if whid:
                infoln("...done")
            else:
                infoln("...failed")
                failed = True
        else:
            infoln("...warehouse exists, skip")
    else:
        infoln("...failed (LSJV Organisation not found)")
        failed = True

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
    infoln("")
    infoln("Remember to assign the SUPPLY_COORDINATOR and SUPPLY_REQUESTER roles manually!")
