# -*- coding: utf-8 -*-
#
# Database upgrade script
#
# RLPPTM Template Version 1.12.6
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/RLPPTM/upgrade/fixup-1.12.6.py
#
import sys

from templates.RLPPTM.config import TESTSTATIONS

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
ftable = s3db.org_facility
htable = s3db.hrm_human_resource

#IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
#TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "RLPPTM")

# -----------------------------------------------------------------------------
# Assign TESTSTATIONS staff to sites
#
if not failed:
    info("Assign test station staff to sites...")

    # Look up all staff of test station organisations without site_id
    join = [otable.on((otable.id == htable.organisation_id)),
            mtable.on((mtable.organisation_id == otable.id) & \
                      (mtable.deleted == False) & \
                      (gtable.id == mtable.group_id) & \
                      (gtable.name == TESTSTATIONS)),
            ]
    query = (htable.site_id == None) & \
            (htable.deleted == False)
    hr_rows = db(query).select(htable.id,
                               htable.person_id,
                               htable.organisation_id,
                               join = join,
                               )
    info("%s records to fix..." % len(hr_rows))

    # Collect the organisation_ids
    org_ids = {row.organisation_id for row in hr_rows}

    # Lookup the facilities belonging to these orgs, oldest first
    query = (ftable.organisation_id.belongs(org_ids)) & \
            (ftable.deleted == False)
    fac_rows = db(query).select(ftable.organisation_id,
                                ftable.site_id,
                                orderby = ftable.created_on,
                                )
    site_ids = {}
    for row in fac_rows:
        if row.organisation_id not in site_ids:
            site_ids[row.organisation_id] = row.site_id

    # Set the site_ids in the staff records
    updated = 0
    for row in hr_rows:
        site_id = site_ids.get(row.organisation_id)
        if site_id:
            updated += 1
            info("+")
            row.update_record(site_id = site_id,
                              modified_by = htable.modified_by,
                              modified_on = htable.modified_on,
                              )
        else:
            info("0")

    infoln("...done (%s records fixed)" % updated)

# -----------------------------------------------------------------------------
# Finishing up
#
if failed:
    db.rollback()
    infoln("UPGRADE FAILED - Action rolled back.")
else:
    db.commit()
    infoln("UPGRADE SUCCESSFUL.")
