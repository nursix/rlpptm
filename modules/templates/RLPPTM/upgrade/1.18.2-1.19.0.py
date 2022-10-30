# Database upgrade script
#
# RLPPTM Template Version 1.18.2 => 1.19.0
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/RLPPTM/upgrade/1.18.2-1.19.0.py
#
import sys

from core import S3Duplicate
from templates.RLPPTM.config import TESTSTATIONS
from templates.RLPPTM.models.org import TestProvider, TestStation

# Override auth (disables all permission checks)
auth.override = True

# Initialize failed-flag
failed = False

# Info
def info(msg):
    sys.stderr.write("%s" % msg)
def infoln(msg):
    sys.stderr.write("%s\n" % msg)

# Load models for tables
otable = s3db.org_organisation
mtable = s3db.org_group_membership
gtable = s3db.org_group

vtable = s3db.org_verification
ctable = s3db.org_commission

ftable = s3db.org_facility
dtable = s3db.org_site_details
atable = s3db.org_site_approval

ottable = s3db.org_organisation_type
tttable = s3db.org_organisation_type_tag
minforeq = tttable.with_alias("minforeq")
verifreq = tttable.with_alias("verifreq")
sttable = s3db.org_site_tag

# Paths
IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "RLPPTM")

# -----------------------------------------------------------------------------
# Upgrade organisation types
#
if not failed:
    info("Upgrade organisation types")

    resource = s3db.resource("org_organisation_type")

    # File and stylesheet paths
    stylesheet = os.path.join(IMPORT_XSLT_FOLDER, "org", "organisation_type.xsl")
    filename = os.path.join(TEMPLATE_FOLDER, "org_organisation_type.csv")

    # Only import relevant type tags, do not update existing ones
    def organisation_type_tag_duplicate(item):
        name = item.data.get("tag")
        if name in ("MINFOREQ",
                    "VERIFREQ",
                    ):
            S3Duplicate(primary = ("organisation_type_id", "tag"),
                        noupdate = True)(item)
        else:
            item.skip = True
    s3db.configure("org_organisation_type_tag",
                   deduplicate = organisation_type_tag_duplicate,
                   )

    # Do not update organisation types themselves
    s3db.configure("org_organisation_type",
                   deduplicate = S3Duplicate(noupdate = True),
                   )

    # Import, capture errors
    try:
        with open(filename, "r") as File:
            resource.import_xml(File,
                                source_type = "csv",
                                stylesheet = stylesheet,
                                )
    except Exception as e:
        error = sys.exc_info()[1] or "unknown error"
    else:
        error = resource.error

    # Fail on any error
    if error:
        infoln("...failed")
        infoln(error)
        failed = True
    else:
        infoln("...done")

# -----------------------------------------------------------------------------
# Add any missing type tags
#
if not failed:
    info("Add missing type tags")

    left = [minforeq.on((minforeq.organisation_type_id == ottable.id) & \
                        (minforeq.tag == "MINFOREQ") & \
                        (minforeq.deleted == False)),
            verifreq.on((verifreq.organisation_type_id == ottable.id) & \
                        (verifreq.tag == "VERIFREQ") & \
                        (verifreq.deleted == False)),
            ]
    query = (ottable.deleted == False) & \
            ((minforeq.id == None) | (verifreq.id == None))
    rows = db(query).select(ottable.id,
                            minforeq.id,
                            verifreq.id,
                            left = left,
                            )

    updated = 0
    for row in rows:
        otype = row.org_organisation_type
        if not row[minforeq.id]:
            tttable.insert(organisation_type_id = otype.id,
                           tag = "MINFOREQ",
                           value = "N",
                           )
        if not row[verifreq.id]:
            tttable.insert(organisation_type_id = otype.id,
                           tag = "VERIFREQ",
                           value = "N",
                           )
        info(".")
        updated += 1

    infoln("...done (%s types fixed)" % updated)

# -----------------------------------------------------------------------------
# Deploy new CMS items
#
if not failed:
    info("Deploy new CMS items")

    resource = s3db.resource("cms_post")

    # File and stylesheet paths
    stylesheet = os.path.join(IMPORT_XSLT_FOLDER, "cms", "post.xsl")
    filename = os.path.join(TEMPLATE_FOLDER, "cms_post.csv")

    # Only import relevant CMS posts, do not update existing ones
    def cms_post_duplicate(item):
        name = item.data.get("name")
        if name in ("...", # TODO select items
                    ):
            S3Duplicate(noupdate=True)(item)
        else:
            item.skip = True
    resource.configure(deduplicate = cms_post_duplicate)

    # Import, capture errors
    try:
        with open(filename, "r") as File:
            resource.import_xml(File,
                                source_type = "csv",
                                stylesheet = stylesheet,
                                )
    except Exception as e:
        error = sys.exc_info()[1] or "unknown error"
    else:
        error = resource.error

    # Fail on any error
    if error:
        infoln("...failed")
        infoln(error)
        failed = True
    else:
        infoln("...done")

# -----------------------------------------------------------------------------
# Generate provider verifications
#
if not failed:
    info("Generate provider verifications")

    left = vtable.on((vtable.organisation_id == otable.id) & \
                     (vtable.deleted == False))
    query = (otable.deleted == False) & \
            (vtable.id == None)
    rows = db(query).select(otable.id, left=left)

    added = 0
    for row in rows:
        provider = TestProvider(row.id)

        # Generate default verification
        verification = provider.verification
        if verification.dhash:
            # Pre-existing record with valid hash => must not update!
            continue

        # Update hash
        update, vhash = provider.vhash()
        update["dhash"] = vhash

        # Mark type as verified if verification is required
        orgtype = update.get("orgtype") or verification.orgtype
        if orgtype != "ACCEPT":
            update["orgtype"] = "VERIFIED"

        # Update accepted-flag
        mgrinfo = update.get("mgrinfo") or verification.mgrinfo
        update["accepted"] = mgrinfo in ("VERIFIED", "ACCEPT")

        # Update verification
        verification.update_record(**update)

        info(".")
        added += 1

    infoln("...done (%s records created)" % added)

# -----------------------------------------------------------------------------
# Upgrade facility approvals
#
if not failed:
    info("Migrate facility approvals")

    mtag = sttable.with_alias("mpav")
    htag = sttable.with_alias("hygiene")
    ltag = sttable.with_alias("layout")
    ptag = sttable.with_alias("public")

    left = [dtable.on((dtable.site_id == ftable.site_id) & \
                      (dtable.deleted == False)),
            mtag.on((mtag.site_id == ftable.site_id) & \
                    (mtag.tag == "MPAV") & \
                    (mtag.deleted == False)),
            htag.on((htag.site_id == ftable.site_id) & \
                    (htag.tag == "HYGIENE") & \
                    (htag.deleted == False)),
            ltag.on((ltag.site_id == ftable.site_id) & \
                    (ltag.tag == "LAYOUT") & \
                    (ltag.deleted == False)),
            ptag.on((ptag.site_id == ftable.site_id) & \
                    (ptag.tag == "PUBLIC") & \
                    (ptag.deleted == False)),
            ]
    query = (ftable.deleted == False)
    rows = db(query).select(ftable.id,
                            ftable.site_id,
                            dtable.authorisation_advice,
                            mtag.id,
                            mtag.value,
                            htag.id,
                            htag.value,
                            ltag.id,
                            ltag.value,
                            ptag.id,
                            ptag.value,
                            left = left,
                            )

    added = 0
    for row in rows:
        ts = TestStation(row.org_facility.site_id)
        approval = ts.approval
        if approval.dhash:
            # Pre-existing approval record - must not update!
            continue

        # Get tag values
        mval = row[mtag.value] if row[mtag.id] else "REVISE"
        hval = row[htag.value] if row[htag.id] else "REVISE"
        lval = row[ltag.value] if row[ltag.id] else "REVISE"
        values = (mval, hval, lval)

        # Determine processing status from tags
        if all(v == "APPROVED" for v in values):
            status = "APPROVED"
        elif any(v == "REVIEW" for v in values):
            status = "REVIEW"
        else:
            status = "REVISE"

        # Determine public-status
        if status == "APPROVED":
            # Keep current value if set, otherwise default to Y
            public = row[ptag.value] if row[ptag.id] else "Y"
            reason = "OVERRIDE" if public == "N" else None
        else:
            # Always N
            public = "N"
            reason = status

        # Update approval record and history
        data = {"mpav": mval,
                "hygiene": hval,
                "layout": lval,
                "status": status,
                "public": public,
                "public_reason": reason,
                "advice": row.org_site_details.authorisation_advice,
                "dhash": ts.vhash()[1],
                }
        approval.update_record(**data)
        ts.update_approval_history()

        info(".")
        added += 1

    infoln("...done (%s records migrated)" % added)

# -----------------------------------------------------------------------------
# Generate provider commissions
#
if not failed:
    info("Generate provider commissions")

    join = [mtable.on((mtable.organisation_id == ftable.organisation_id) & \
                      (mtable.deleted == False) & \
                      (gtable.id == mtable.group_id) & \
                      (gtable.name == TESTSTATIONS) & \
                      (gtable.deleted == False)),
            atable.on((atable.site_id == ftable.site_id) & \
                      (atable.public == "Y") & \
                      (atable.deleted == False)),
            ]
    left = ctable.on((ctable.organisation_id == ftable.organisation_id) & \
                     (ctable.deleted == False))
    query = (ctable.id == None) & \
            (ftable.deleted == False)
    rows = db(query).select(ftable.organisation_id,
                            groupby = ftable.organisation_id,
                            left = left,
                            join = join,
                            )

    today = datetime.datetime.utcnow().date()
    end = datetime.date(2022, 11, 24)

    info("...")
    generated, suspended = 0, 0
    for row in rows:
        provider = TestProvider(row.organisation_id)
        if end < today:
            status, reason = "EXPIRED", None
        elif provider.verification.accepted:
            status, reason = "CURRENT", None
        else:
            status, reason = "SUSPENDED", "N/V"

        data = {"organisation_id": provider.organisation_id,
                "date": today,
                "end_date": end,
                "status": status,
                "prev_status": "CURRENT",
                "status_date": today,
                "status_reason": reason,
                #"comments": "*** automatisch generiert ***",
                }
        record_id = data["id"] = ctable.insert(**data)
        generated += 1

        if status != "CURRENT":
            reason = "SUSPENDED" if status == "SUSPENDED" else "COMMISSION"
            TestStation.update_all(provider.organisation_id,
                                   public = "N",
                                   reason = reason,
                                   )
            suspended += 1
            info("-")
        else:
            info("+")

    infoln("...done (%s commissions generated, %s of which suspended)" % (generated, suspended))

# -----------------------------------------------------------------------------
# Upgrade user roles
#
if not failed:
    info("Upgrade user roles")

    bi = s3base.BulkImporter()
    filename = os.path.join(TEMPLATE_FOLDER, "auth_roles.csv")

    try:
        error = bi.import_roles(filename)
    except Exception as e:
        error = sys.exc_info()[1] or "unknown error"
    if error:
        infoln("...failed")
        infoln(error)
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

# END =========================================================================
