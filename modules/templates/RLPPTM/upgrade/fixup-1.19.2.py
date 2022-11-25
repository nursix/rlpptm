# Database upgrade script
#
# RLPPTM Template Version 1.19.1
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/RLPPTM/upgrade/fixup-1.19.1.py
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
# Fix end date of commissions
#
if not failed:
    info("Fix end date of commissions...")

    old = datetime.date(2022,11,24)
    new = datetime.date(2022,11,25)

    query = (ctable.end_date == old) & \
            (ctable.deleted == False)
    updated = db(query).update(end_date = new,
                               modified_by = ctable.modified_by,
                               modified_on = ctable.modified_on,
                               )

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
