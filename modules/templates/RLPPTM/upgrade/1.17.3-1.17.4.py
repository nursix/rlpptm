# Database upgrade script
#
# RLPPTM Template Version 1.17.3 => 1.17.4
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/RLPPTM/upgrade/1.17.3-1.17.4.py
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
# Mark all previous newsletters as read
#
if not failed:
    infoln("Mark newsletters as read...")

    utable = auth.settings.table_user
    mtable = auth.settings.table_membership
    sr = auth.get_system_roles()

    join = utable.on(utable.id == mtable.user_id)
    query = (mtable.group_id == sr.ORG_ADMIN) & \
            (mtable.deleted == False)
    rows = db(query).select(utable.id,
                            utable.email,
                            join = join,
                            )
    updated = 0
    for row in rows:
        info("%s..." % row.email)
        auth.override = False # for accessible-queries to work ;)
        auth.s3_impersonate(row.id)
        unread = s3db.cms_unread_newsletters(count=False, cached=False)
        if unread:
            info("(%s newsletters)" % len(unread))
            s3db.cms_mark_newsletter(unread)
            infoln("...all marked as read")
        else:
            infoln("...no unread newsletters")
        auth.s3_impersonate(None)
        auth.override = True
        updated += 1

    infoln("...done (%s users updated)" % updated)

# -----------------------------------------------------------------------------
# Fix role assignments
#
if not failed:
    info("Fix role assignments")

    table = auth.settings.table_membership
    updated = db(table.id > 0).update(system=False)
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
