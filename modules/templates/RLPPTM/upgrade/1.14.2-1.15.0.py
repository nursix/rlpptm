# -*- coding: utf-8 -*-
#
# Database upgrade script
#
# RLPPTM Template Version 1.14.2 => 1.15.0
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/RLPPTM/upgrade/1.14.2-1.15.0.py
#
import sys

#from gluon.storage import Storage
#from gluon.tools import callback
#from core import S3Duplicate

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
#ftable = s3db.org_facility

IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "RLPPTM")

# -----------------------------------------------------------------------------
# Fix consent assertions
#
if not failed:
    info("Fix consent assertions...")

    from core import ConsentTracking

    cotable = s3db.auth_consent_option
    catable = s3db.auth_consent_assertion

    rows = db(cotable.id>0).select(cotable.id,
                                   cotable.name,
                                   cotable.description,
                                   )
    options = {}
    for row in rows:
        option = (("name", row.name), ("description", row.description))
        options[row.id] = ConsentTracking.get_hash(option)

    rows = db(catable.id>0).select(catable.id,
                                   catable.person_id,
                                   catable.context,
                                   catable.date,
                                   catable.option_id,
                                   catable.vhash,
                                   )
    updated, failures = 0, 0
    for row in rows:
        ohash = options.get(row.option_id)
        if not ohash:
            info("-")
            failures += 1
            continue
        consent = (("person_id", row.person_id),
                   ("context", row.context),
                   ("date", row.date.isoformat()),
                   ("option_id", row.option_id),
                   ("consented", True),
                   ("ohash", ohash),
                   )
        vhash = ConsentTracking.get_hash(consent)
        if vhash == row.vhash:
            info("=")
            continue
        info(".")
        row.update_record(consented=True, vhash=vhash)
        updated += 1

    infoln("...done (%s records updated, %s updates failed)" % (updated, failures))

# -----------------------------------------------------------------------------
# Fix consent hashes
#
if not failed:
    info("Fix consent hashes...")

    from core import ConsentTracking

    cotable = s3db.auth_consent_option
    ctable = s3db.auth_consent

    rows = db(cotable.id>0).select(cotable.id,
                                   cotable.name,
                                   cotable.description,
                                   )
    options = {}
    for row in rows:
        option = (("name", row.name), ("description", row.description))
        options[row.id] = ConsentTracking.get_hash(option)

    rows = db(ctable.id>0).select(ctable.id,
                                  ctable.person_id,
                                  ctable.date,
                                  ctable.option_id,
                                  ctable.vsign,
                                  ctable.consenting,
                                  ctable.vhash,
                                  )
    updated, failures = 0, 0
    for row in rows:
        ohash = options.get(row.option_id)
        if not ohash:
            info("-")
            failures += 1
            continue
        consent = (("date", row.date.isoformat()),
                   ("option_id", row.option_id),
                   ("person_id", row.person_id),
                   ("vsign", row.vsign),
                   ("consenting", row.consenting),
                   ("ohash", ohash),
                   )

        vhash = ConsentTracking.get_hash(consent)
        if vhash == row.vhash:
            info("=")
            continue
        row.update_record(vhash=vhash)
        if not ConsentTracking.verify(row.id):
            infoln("...invalid hash")
            failed = True
        info(".")
        updated += 1

    infoln("...done (%s records updated, %s updates failed)" % (updated, failures))

# -----------------------------------------------------------------------------
# Deploy new processing types
#
if not failed:
    info("Deploy new processing types")

    # File and Stylesheet Paths
    stylesheet = os.path.join(IMPORT_XSLT_FOLDER, "auth", "processing_type.xsl")
    filename = os.path.join(TEMPLATE_FOLDER, "auth_processing_type.csv")

    # Only import relevant items
    def auth_processing_type_duplicate(item):
        code = item.data.get("code")
        if code in ("TPNDO",
                    ):
            S3Duplicate(primary=("code",), noupdate=True)(item)
        else:
            item.skip = True

    # Import, fail on any errors
    try:
        with open(filename, "r") as File:
            resource = s3db.resource("auth_processing_type")
            resource.configure(deduplicate=auth_processing_type_duplicate)
            resource.import_xml(File, source_type="csv", stylesheet=stylesheet)
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
