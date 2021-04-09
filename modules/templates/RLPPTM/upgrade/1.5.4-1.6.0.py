# -*- coding: utf-8 -*-
#
# Database upgrade script
#
# RLPPTM Template Version 1.5.4 => 1.6.0
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/RLPPTM/upgrade/1.5.4-1.6.0.py
#
#import datetime
import sys
import uuid
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
ptable = s3db.fin_voucher_program
ttable = s3db.fin_voucher_transaction
otable = s3db.org_organisation
ottable = s3db.org_organisation_tag
mtable = s3db.org_group_membership
gtable = s3db.org_group
ftable = s3db.org_facility
sttable = s3db.org_site_tag

IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "RLPPTM")

# -----------------------------------------------------------------------------
# Correct balances in voucher programs
#
if not failed:
    infoln("Fix voucher program balances...")

    # Get all programs
    query = (ptable.deleted == False)
    programs = db(query).select(ptable.id,
                                ptable.credit,
                                ptable.compensation,
                                )

    for program in programs:
        info("Program #%s: " % program.id)

        data = {}

        # Look up current balances from transaction table
        query = (ttable.program_id == program.id) & \
                (ttable.deleted == False)
        credit = ttable.credit.sum()
        compensation = ttable.compensation.sum()
        balance = db(query).select(credit,
                                   compensation,
                                   ).first()

        # Check credit balance
        credit_balance = balance[credit]
        if program.credit != credit_balance:
            data["credit"] = credit_balance
            info("(credit %s => %s) " % (program.credit, credit_balance))

        # Check compensation balance
        compensation_balance = balance[compensation]
        if program.compensation != compensation_balance:
            data["compensation"] = compensation_balance
            info("(compensation %s => %s) " % (program.compensation, compensation_balance))

        # Update as necessary
        if data:
            program.update_record(**data)
            infoln("...fixed")
        else:
            infoln("...checked ok")

    infoln("...done")

# -----------------------------------------------------------------------------
# Add OrgID-tag for all organisations
#
if not failed:
    info("Install missing OrgID-Tags")

    # Get all organisations which do not have a tag yet
    left = ttable.on((ottable.organisation_id == otable.id) & \
                     (ottable.tag == "OrgID") & \
                     (ottable.deleted == False))

    query = (otable.deleted == False) & \
            (ottable.id == None)
    organisations = db(query).select(otable.id,
                                     otable.uuid,
                                     left = left,
                                     )

    added = 0
    for organisation in organisations:
        try:
            uid = int(organisation.uuid[9:14], 16)
        except (TypeError, ValueError):
            uid = int(uuid.uuid4().urn[9:14], 16)

        value = "%06d%04d" % (uid, organisation.id)
        ottable.insert(organisation_id = organisation.id,
                       tag = "OrgID",
                       value = value,
                       )
        added += 1

    infoln("...done (%s tags added)" % added)

# -----------------------------------------------------------------------------
# Add public-tags for all test stations
#
if not failed:
    info("Add public-tag for all test stations")

    from templates.RLPPTM.config import TESTSTATIONS

    join = [mtable.on((mtable.organisation_id == ftable.organisation_id) & \
                      (mtable.deleted == False)),
            gtable.on((gtable.id == mtable.group_id) & \
                      (gtable.name == TESTSTATIONS))
            ]

    left = [sttable.on((sttable.site_id == ftable.site_id) & \
                       (sttable.tag == "PUBLIC") & \
                       (sttable.deleted == False)),
            ]

    query = (ftable.obsolete == False) & \
            (ftable.deleted == False)
    rows = db(query).select(ftable.id,
                            ftable.site_id,
                            sttable.id,
                            join = join,
                            left = left,
                            )
    added = 0
    for row in rows:
        facility = row.org_facility
        tag = row.org_site_tag
        if not tag.id:
            success = sttable.insert(site_id = facility.site_id,
                                     tag = "PUBLIC",
                                     value = "Y",
                                     )
            if success:
                added += 1
            else:
                failed = True
                infoln("...failed")
                break
    if not failed:
        infoln("..done (%s tags added)" % added)

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
