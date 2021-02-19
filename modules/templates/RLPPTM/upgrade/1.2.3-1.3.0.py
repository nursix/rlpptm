# -*- coding: utf-8 -*-
#
# Database upgrade script
#
# RLPPTM Template Version 1.2.3 => 1.3.0
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/RLPPTM/upgrade/1.2.3-1.3.0.py
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
vtable = s3db.fin_voucher
ttable = s3db.fin_voucher_transaction

IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "RLPPTM")

# -----------------------------------------------------------------------------
# Set initial credit for existing vouchers
#
if not failed:
    info("Set initial credit for vouchers")

    query = (vtable.initial_credit == None) & \
            (vtable.deleted == False)
    try:
        updated = db(query).update(initial_credit = 1,
                                   modified_on = vtable.modified_on,
                                   modified_by = vtable.modified_by,
                                   )
    except:
        infoln("...failed")
        infoln(sys.exc_info()[1])
        failed = True
    else:
        infoln("...done (%s records updated)" % updated)

# -----------------------------------------------------------------------------
# Set existing vouchers to single-debit
#
if not failed:
    info("Set all vouchers to single-debit")

    query = ((vtable.single_debit == None) | (vtable.single_debit == False)) & \
            (vtable.deleted == False)
    try:
        updated = db(query).update(single_debit = True,
                                   modified_on = vtable.modified_on,
                                   modified_by = vtable.modified_by,
                                   )
    except:
        infoln("...failed")
        infoln(sys.exc_info()[1])
        failed = True
    else:
        infoln("...done (%s records updated)" % updated)

# -----------------------------------------------------------------------------
# Set credit_spent for all vouchers
#
if not failed:
    info("Initialize credit spent for vouchers")

    query = (vtable.credit_spent == None) & \
            (vtable.deleted == False)
    try:
        updated = db(query).update(credit_spent = 0,
                                   modified_on = vtable.modified_on,
                                   modified_by = vtable.modified_by,
                                   )
    except:
        infoln("...failed")
        infoln(sys.exc_info()[1])
        failed = True
    else:
        infoln("...done (%s records updated)" % updated)

if not failed:
    info("Set credit spent for all redeemed vouchers")

    left = ttable.on((ttable.voucher_id == vtable.id) & \
                     (ttable.type == "DBT") & \
                     (ttable.voucher != None) & \
                     (ttable.deleted == False))
    query = (vtable.credit_spent == 0) & \
            (vtable.balance == 0) & \
            (vtable.deleted == False) & \
            (ttable.id != None)
    total = ttable.voucher.sum()
    rows = db(query).select(vtable.id,
                            total,
                            groupby = vtable.id,
                            left = left,
                            )

    updated = 0
    for row in rows:
        voucher = row.fin_voucher
        credit_spent = -row[total]
        try:
            voucher.update_record(credit_spent = credit_spent,
                                  modified_on = vtable.modified_on,
                                  modified_by = vtable.modified_by,
                                  )
        except:
            infoln("...failed")
            infoln(sys.exc_info()[1])
            failed = True
            break
        else:
            updated += 1

    if not failed:
        infoln("...done (%s records updated)" % updated)

# -----------------------------------------------------------------------------
# Deploy new CMS items
#
if not failed:
    info("Deploy new CMS items")

    # File and Stylesheet Paths
    stylesheet = os.path.join(IMPORT_XSLT_FOLDER, "cms", "post.xsl")
    filename = os.path.join(TEMPLATE_FOLDER, "cms_post.csv")

    # Only import relevant CMS posts, do not update any existing ones
    def cms_post_duplicate(item):
        name = item.data.get("name")
        if name in ("BearerDoBIntro", "GroupDoBIntro"):
            S3Duplicate(noupdate=True)(item)
        else:
            item.skip = True

    # Import, fail on any errors
    try:
        with open(filename, "r") as File:
            resource = s3db.resource("cms_post")
            resource.configure(deduplicate = cms_post_duplicate)
            resource.import_xml(File,
                                format = "csv",
                                stylesheet = stylesheet,
                                )
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
