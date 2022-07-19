# Database upgrade script
#
# RLPPTM Template Version 1.18.1 => 1.18.2
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/RLPPTM/upgrade/1.18.1-1.18.2.py
#
import sys

#from core import S3Duplicate
from templates.RLPPTM.config import TESTSTATIONS
from templates.RLPPTM.customise.org import facility_approval_hash, update_mgrinfo

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
#otable = s3db.org_organisation

IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "RLPPTM")

# -----------------------------------------------------------------------------
# Add verification has for all test stations
#
if not failed:
    info("Add verification hashes for all test stations...")

    ftable = s3db.org_facility
    ttable = s3db.org_site_tag
    dtable = ttable.with_alias("dhash_tag")
    left = [ttable.on((ttable.site_id == ftable.site_id) & \
                      (ttable.tag == "STATUS") & \
                      (ttable.deleted == False)),
            dtable.on((dtable.site_id == ftable.site_id) & \
                      (dtable.tag == "DHASH") & \
                      (dtable.deleted == False)),
            ]
    query = (ftable.deleted == False)

    rows = db(query).select(ftable.id,
                            ftable.site_id,
                            ftable.location_id,
                            ttable.id,
                            ttable.value,
                            dtable.id,
                            dtable.value,
                            left=left,
                            )

    updated, added = 0, 0
    for row in rows:
        facility = row.org_facility
        site_id = facility.site_id

        status = row.org_site_tag.value
        if status == "APPROVED":
            vhash = facility_approval_hash({}, site_id, facility.location_id)[1]
        else:
            vhash = None

        dhash = row[dtable._tablename]
        if dhash.id:
            dhash.update_record(value = vhash)
            updated += 1
            info(".")
        else:
            ttable.insert(site_id = site_id,
                          tag = "DHASH",
                          value = vhash,
                          )
            added += 1
            info("+")

    infoln("...done (%s hashes added, %s updated)" % (added, updated))

# -----------------------------------------------------------------------------
# Update MGRINFO status for all test station organisations
#
if not failed:
    info("Update manager info status for all test stations...")

    otable = s3db.org_organisation
    gtable = s3db.org_group
    mtable = s3db.org_group_membership

    join = gtable.on((mtable.organisation_id == otable.id) & \
                     (mtable.deleted == False) & \
                     (gtable.id == mtable.group_id) & \
                     (gtable.name == TESTSTATIONS))
    query = (otable.deleted == False)

    rows = db(query).select(otable.id)
    for row in rows:
        update_mgrinfo(row.id)
        info(".")

    infoln("...done (%s organisations updated)" % len(rows))

# -----------------------------------------------------------------------------
# Finishing up
#
if failed:
    db.rollback()
    infoln("UPGRADE FAILED - Action rolled back.")
else:
    db.commit()
    infoln("UPGRADE SUCCESSFUL.")
