# Database upgrade script
#
# RLPPTM Template Version 1.19.0 => 1.19.1
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/RLPPTM/upgrade/1.19.0-1.19.1.py
#
import sys

#from core import S3Duplicate

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
ctable = s3db.org_commission

# Paths
IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "RLPPTM")

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
# Fix status/prev_status discrepancy
#
if not failed:
    info("Fix commission statuses")

    query = (ctable.status != ctable.prev_status) & \
            (ctable.deleted == False)
    updated = db(query).update(prev_status = ctable.status,
                               modified_on = ctable.modified_on,
                               modified_by = ctable.modified_by,
                               )
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

# END =========================================================================
