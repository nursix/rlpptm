# -*- coding: utf-8 -*-
#
# Database upgrade script
#
# RLPPTM Template Version 1.10.1 => 1.11.0
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/RLPPTM/upgrade/1.10.1-1.11.0.py
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
otable = s3db.org_organisation
gtable = s3db.org_group
mtable = s3db.org_group_membership

IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "RLPPTM")

# -----------------------------------------------------------------------------
# Deploy supply item categories
#
if not failed:
    info("Deploy supply item categories")

    # File and Stylesheet Paths
    stylesheet = os.path.join(IMPORT_XSLT_FOLDER, "supply", "item_category.xsl")
    filename = os.path.join(TEMPLATE_FOLDER, "supply_item_category.csv")

    # Import, fail on any errors
    try:
        with open(filename, "r") as File:
            resource = s3db.resource("supply_item_category")
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
# Add DELIVERY-tags
#
if not failed:
    info("Add DELIVERY-tags for test stations")

    from templates.RLPPTM.config import TESTSTATIONS
    join = [mtable.on((mtable.organisation_id == otable.id) & \
                      (mtable.deleted == False) & \
                      (gtable.id == mtable.group_id) & \
                      (gtable.name == TESTSTATIONS)),
            ]

    ttable = s3db.org_organisation_tag
    rtable = ttable.with_alias("requester")
    dtable = ttable.with_alias("delivery")

    left = [rtable.on((rtable.organisation_id == otable.id) & \
                      (rtable.tag == "REQUESTER") & \
                      (rtable.deleted == False)),
            dtable.on((dtable.organisation_id == otable.id) & \
                      (dtable.tag == "DELIVERY") & \
                      (dtable.deleted == False)),
            ]
    query = (otable.deleted == False)
    rows = db(query).select(otable.id,
                            rtable.id,
                            rtable.value,
                            dtable.id,
                            dtable.value,
                            join = join,
                            left = left,
                            )
    added = 0
    for row in rows:
        organisation = row.org_organisation
        requester = row.requester
        delivery = row.delivery
        if not delivery.id:
            v = "VIA_DC" if requester.id and requester.value == "Y" else "DIRECT"
            ttable.insert(organisation_id = organisation.id,
                          tag = "DELIVERY",
                          value = v,
                          )
            added += 1
    infoln("...done (%s tags added)" % added)

# -----------------------------------------------------------------------------
# Add CENTRAL-tags
#
if not failed:
    info("Add CENTRAL-tags for warehouses")

    wtable = s3db.inv_warehouse
    ttable = s3db.org_site_tag

    left = ttable.on((ttable.site_id == wtable.site_id) & \
                     (ttable.tag == "CENTRAL") & \
                     (ttable.deleted == False))
    query = (wtable.deleted == False)
    rows = db(query).select(wtable.site_id,
                            ttable.id,
                            left = left,
                            )
    added = 0
    for row in rows:
        warehouse = row.inv_warehouse
        central = row.org_site_tag

        if not central.id:
            ttable.insert(site_id = warehouse.site_id,
                          tag = "CENTRAL",
                          value = "N",
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
