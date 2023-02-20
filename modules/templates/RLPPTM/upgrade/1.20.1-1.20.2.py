# Database upgrade script
#
# RLPPTM Template Version 1.20.1 => 1.20.2
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/RLPPTM/upgrade/1.20.1-1.20.2.py
#
import sys

#from core import S3Duplicate
from templates.RLPPTM.models.org import TestProvider

# Override auth (disables all permission checks)
auth.override = True

# Initialize failed-flag
failed = False

# Info
def info(msg):
    sys.stderr.write("%s" % msg)
    sys.stderr.flush()
def infoln(msg):
    sys.stderr.write("%s\n" % msg)
    sys.stderr.flush()

# Load models for tables
vtable = s3db.org_verification

# Paths
IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "RLPPTM")

# -----------------------------------------------------------------------------
# Deploy new CMS items
#
if not failed:
    info("Fix provider verifications")

    query = (vtable.deleted == False)
    rows = db(query).select(vtable.organisation_id)

    tags = ("orgtype", "mpav", "reprinfo", "status")

    updated = 0
    for row in rows:
        provider = TestProvider(row.organisation_id)

        update = provider.verification_defaults()

        verification = provider.verification
        for tag in tags[:2]:
            if update[tag] in ("N/A", "ACCEPT", "VERIFIED"):
                continue
            current_value = verification[tag]
            if current_value == "ACCEPT":
                update[tag] = "REVIEW"
            else:
                update[tag] = current_value


        status = update["status"] = provider.status(update[t] for t in tags[:3])

        if any(update[k] != verification[k] for k in tags):
            verification.update_record(**update)

            if status == "COMPLETE":
                provider.reinstate_commission("N/V")
            else:
                provider.suspend_commission("N/V")
            info("+")
            updated += 1
        else:
            info(".")

    infoln("...done (%s records updated)" % updated)

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
