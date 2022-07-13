# Database upgrade script
#
# RLPPTM Template Version 1.18.0 => 1.18.1
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/RLPPTM/upgrade/1.18.0-1.18.1.py
#
import sys

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
#otable = s3db.org_organisation

IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "RLPPTM")

# -----------------------------------------------------------------------------
# Remove role assignments for deleted entities
#
if not failed:
    infoln("Remove obsolete role assignments...")

    mtable = auth.settings.table_membership
    etable = s3db.pr_pentity

    left = etable.on(etable.pe_id == mtable.pe_id)
    query = (mtable.pe_id != None) & \
            (mtable.pe_id != 0) & \
            (mtable.deleted == False) & \
            ((etable.pe_id == None) | (etable.deleted == True))
    rows = db(query).select(mtable.id,
                            mtable.user_id,
                            mtable.group_id,
                            mtable.pe_id,
                            left = left,
                            )
    info("...found %s obsolete assignments..." % len(rows))
    removed = 0
    for row in rows:
        auth.s3_remove_role(row.user_id,
                            row.group_id,
                            for_pe = row.pe_id,
                            )
        info(".")
        removed += 1
    infoln("...done (%s removed)." % removed)

# -----------------------------------------------------------------------------
# Finishing up
#
if failed:
    db.rollback()
    infoln("UPGRADE FAILED - Action rolled back.")
else:
    db.commit()
    infoln("UPGRADE SUCCESSFUL.")
