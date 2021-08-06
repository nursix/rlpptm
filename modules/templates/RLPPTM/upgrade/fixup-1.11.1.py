# -*- coding: utf-8 -*-
#
# Database upgrade script
#
# RLPPTM Template Version 1.11.1
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/RLPPTM/upgrade/fixup-1.11.1.py
#
import sys

#from gluon.storage import Storage
#from gluon.tools import callback
#from s3 import S3Duplicate

TAGNAME = "DELIVERY"
TAGVALUE = "VIA_DC"
ORGTYPE = "Kommunale Teststelle"

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
ttable = s3db.org_organisation_tag
ltable = s3db.org_organisation_organisation_type

IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "RLPPTM")

# -----------------------------------------------------------------------------
# Assign Organisation Types after DELIVERY-Tag
#
if not failed:
    info("Assign organisation types after DELIVERY-tag")

    ottable = s3db.org_organisation_type
    if isinstance(ORGTYPE, str) and not ORGTYPE.isdigit():
        query = (ottable.name == ORGTYPE)
    else:
        query = (ottable.id == ORGTYPE)
    query &= (ottable.deleted == False)
    row = db(query).select(ottable.id,
                           limitby = (0, 1),
                           ).first()
    if not row:
        infoln("...failed (organisation type not found)")
    else:
        organisation_type_id = row.id

if not failed:
    from templates.RLPPTM.config import TESTSTATIONS
    join = [mtable.on((mtable.organisation_id == otable.id) & \
                      (mtable.deleted == False) & \
                      (gtable.id == mtable.group_id) & \
                      (gtable.name == TESTSTATIONS)),
            ttable.on((ttable.organisation_id == otable.id) & \
                      (ttable.tag == TAGNAME) & \
                      (ttable.value == TAGVALUE) & \
                      (ttable.deleted == False)),
            ]

    left = [ltable.on((ltable.organisation_id == otable.id) & \
                      (ltable.deleted == False)),
            ]

    query = (otable.deleted == False) & \
            (ltable.id == None)
    rows = db(query).select(otable.id,
                            join = join,
                            left = left,
                            )

    set_record_owner = auth.s3_set_record_owner
    s3db_onaccept = s3db.onaccept

    info("...(%s type-less organisations found)..." % len(rows))

    added = 0
    for row in rows:
        link = {"organisation_id": row.id,
                "organisation_type_id": organisation_type_id,
                }
        link_id = link["id"] = ltable.insert(**link)
        if link_id:
            set_record_owner(ltable, link)
            s3db_onaccept(ltable, link, method="create")
            added += 1
            info("+")
        else:
            failed = True
            break

    if not failed:
        infoln("...done (%s links added)" % added)
    else:
        infoln("...failed (link insertion failed)")

# -----------------------------------------------------------------------------
# Finishing up
#
if failed:
    db.rollback()
    infoln("UPGRADE FAILED - Action rolled back.")
else:
    db.commit()
    infoln("UPGRADE SUCCESSFUL.")
