# Database upgrade script
#
# RLPPTM Template Version 1.19.1 => 1.19.2
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/RLPPTM/upgrade/1.19.1-1.19.2.py
#
import sys

#from core import S3Duplicate
from templates.RLPPTM.config import TESTSTATIONS
from templates.RLPPTM.models.org import TestProvider

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
ttable = s3db.org_organisation_type_tag
rtable = s3db.org_requirements
vtable = s3db.org_verification
ftable = s3db.org_facility
atable = s3db.org_site_approval

# Paths
IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "RLPPTM")

# -----------------------------------------------------------------------------
# Migrate to Org Requirements
#
if not failed:
    info("Migrate to organisation requirements...")

    tags = {"Commercial": "commercial",
            "VERIFREQ": "verifreq",
            "MINFOREQ": "minforeq",
            }

    query = (ttable.tag in list(tags.keys())) & \
            (ttable.deleted == False)

    rows = db(query).select(ttable.organisation_type_id,
                            ttable.tag,
                            ttable.value,
                            )
    types = {}
    for row in rows:
        type_id = row.organisation_type_id
        if type_id not in types:
            requirements = types[type_id] = {}
        else:
            requirements = types[type_id]
        tag = tags.get(row.tag)
        if tag:
            requirements[tag] = row.value == "Y"

    added = 0
    for type_id, flags in types.items():
        if any(flags.values()):
            query = (rtable.organisation_type_id == type_id) & \
                    (rtable.deleted == False)
            row = db(query).select(rtable.id, limitby = (0, 1)).first()
            if not row:
                flags["organisation_type_id"] = type_id
                rtable.insert(**flags)
                added += 1
                info("+")

    # Fix missing tags
    db(rtable.natpersn==None).update(natpersn=False)
    db(rtable.mpavreq==None).update(mpavreq=False)

    infoln("...done (%s organisation types migrated)" % added)

# -----------------------------------------------------------------------------
# Establish MPAV requirement
#
if not failed:
    info("Establish MPAV requirement")

    join = [ttable.on((ttable.organisation_type_id == rtable.organisation_type_id) & \
                      (ttable.tag == "OrgGroup") & \
                      (ttable.value == TESTSTATIONS) & \
                      (ttable.deleted == False)),
            ]

    query = (rtable.modified_by == None) & \
            (rtable.deleted == False)
    subset = db(query)._select(rtable.id, join=join)
    updated = db(rtable.id.belongs(subset)).update(mpavreq=True)

    infoln("...done (%s records updated)" % updated)

# -----------------------------------------------------------------------------
# Update Org verifications
#
if not failed:
    info("Update organisation verification status...")

    updated = 0

    query = (vtable.deleted == False)
    rows = db(query).select(vtable.id,
                            vtable.organisation_id,
                            vtable.mgrinfo,
                            vtable.orgtype,
                            vtable.status,
                            )
    for row in rows:
        update = {}
        mgrinfo = row.mgrinfo
        orgtype = row.orgtype

        if mgrinfo == "COMPLETE":
            mgrinfo = update["mgrinfo"] = "VERIFIED"
        elif mgrinfo == "REVISE":
            provider = TestProvider(row.organisation_id)
            if provider.minforeq:
                status = provider.check_mgrinfo()
                if mgrinfo != status:
                    mgrinfo = update["mgrinfo"] = status
            elif mgrinfo != "ACCEPT":
                update["mgrinfo"] = "ACCEPT"

        if orgtype == "N/V":
            org_type = update["orgtype"] = "REVIEW"

        if all(status in ("ACCEPT", "VERIFIED") for status in (mgrinfo, orgtype)):
            status = "COMPLETE"
        elif any(status == "REVIEW" for status in (mgrinfo, orgtype)):
            status = "REVIEW"
        else:
            status = "REVISE"
        if status != row.status:
            update["status"] = status

        if update:
            update["modified_on"] = vtable.modified_on
            update["modified_by"] = vtable.modified_by
            row.update_record(**update)
            updated += 1
            info("*")
        else:
            info(".")

    infoln("...done (%s records updated)" % updated)

# -----------------------------------------------------------------------------
# Set MPAV status
#
if not failed:
    info("Set MPAV status...")

    left = atable.on((atable.site_id == ftable.site_id) & \
                     (atable.deleted == False))
    rows = db(ftable.deleted == False).select(ftable.site_id,
                                              ftable.organisation_id,
                                              atable.hygiene,
                                              atable.layout,
                                              atable.mpav,
                                              atable.status,
                                              left=left,
                                              )

    modified = set()
    for row in rows:
        facility = row[ftable]
        approval = row[atable]

        organisation_id = facility.organisation_id
        provider = TestProvider(organisation_id)
        verification = provider.verification

        update = {}
        if provider.mpavreq:
            if verification.mpav == "VERIFIED":
                continue
            if approval.mpav == "APPROVED":
                update["mpav"] = "VERIFIED"
            elif verification.mpav != "REVIEW":
                update["mpav"] = "REVISE"
        else:
            # Always accept
            if verification.mpav != "ACCEPT":
                update["mpav"] = "ACCEPT"
        if update:
            update["modified_by"] = vtable.modified_by
            update["modified_on"] = vtable.modified_on
            verification.update_record(**update)
            modified.add(organisation_id)
            info("+")
        else:
            info("-")

    for organisation_id in modified:
        provider = TestProvider(organisation_id)
        provider.update_verification()

    infoln("...done (status of %s organisations updated)" % len(modified))

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
