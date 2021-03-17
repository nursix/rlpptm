# -*- coding: utf-8 -*-
#
# Database upgrade script
#
# RLPPTM Template Version 1.4.2 => 1.5.0
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/RLPPTM/upgrade/1.4.2-1.5.0.py
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
mtable = auth.settings.table_membership
otable = s3db.org_organisation
gtable = s3db.org_group
ltable = s3db.org_group_membership
ptable = s3db.fin_voucher_program

IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "RLPPTM")

# -----------------------------------------------------------------------------
# Grant PROVIDER_ACCOUNTANT role to all org-admins in the teststation group
#
if not failed:
    info("Assign provider accountant role to all test station admins")

    # Look up the pe_ids of all test stations
    from templates.RLPPTM.config import TESTSTATIONS
    join = [ltable.on((ltable.organisation_id == otable.id) & \
                      (ltable.deleted == False)),
            gtable.on((gtable.id == ltable.group_id) & \
                      (gtable.name == TESTSTATIONS) & \
                      (gtable.deleted == False)),
            ]
    query = (otable.deleted == False)
    organisations = db(query).select(otable.pe_id, join=join)
    pe_ids = list(set(org.pe_id for org in organisations))

    info("...(%s organisations)" % len(pe_ids))

    # Get all users within these realms
    users = s3db.pr_realm_users(pe_ids) if pe_ids else None
    if users:
        checked = 0
        # Look up those among the realm users who have
        # the role for either pe_id or for their default realm
        rtable = auth.settings.table_group
        mtable = auth.settings.table_membership
        ltable = s3db.pr_person_user
        ORG_ADMIN = auth.get_system_roles().ORG_ADMIN
        query = (mtable.user_id.belongs(users.keys())) & \
                (mtable.group_id == ORG_ADMIN) & \
                ((mtable.pe_id == None) | (mtable.pe_id.belongs(pe_ids))) & \
                (mtable.deleted == False)
        rows = db(query).select(mtable.user_id)
        user_ids = set(row.user_id for row in rows)

        # Assign them the accountant role
        for user_id in user_ids:
            info(".")
            auth.s3_assign_role(user_id, "PROVIDER_ACCOUNTANT")
            checked += 1

        infoln("...done (%s users checked)" % checked)
    else:
        infoln("...skip (no users found)")

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
        if name in ("Subject ClaimNotification",
                    "Message ClaimNotification",
                    "Subject InvoiceSettled",
                    "Message InvoiceSettled",
                    ):
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
# Make sure the voucher programs have a unit, price_per_unit and currency set
#
if not failed:
    info("Make sure voucher programs have billing data")
    programs = db(ptable.deleted == False).select(ptable.id,
                                                  ptable.unit,
                                                  ptable.price_per_unit,
                                                  ptable.currency,
                                                  )
    updated = 0
    for program in programs:
        data = {}
        if not ptable.unit:
            data["unit"] = "Tests"
        if not ptable.price_per_unit:
            data["price_per_unit"] = 39.0
        if not ptable.currency:
            data["currency"] = "EUR"
        if data:
            info(".")
            program.update_record(**data)
            updated += 1

    infoln("...done (%s programs updated)" % updated)

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
