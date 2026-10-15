# Database upgrade script
#
# RLPPTM Template Version 1.21.2
#
# Execute in web2py folder before code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/RLPPTM/upgrade/prep-1.22.0.py
#
import os
import sys
import datetime

from core import S3Duplicate

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
ndtable = s3db.cms_newsletter_distribution
pftable = s3db.pr_filter

# Paths
IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "RLPPTM")

settings.base.debug = True

# -----------------------------------------------------------------------------
# Backup newsletter distribution links
#
if not failed:
    info("Backup newsletter distribution links")

    if "filter_id" in ndtable.fields:

        bkp_tablename = "cms_newsletter_distribution_backup"
        bkp_table = s3db.table(bkp_tablename)
        if not bkp_table:
            # Temporarily define cms_newsletter_distribution_backup
            db.define_table(bkp_tablename,
                            Field("filter_uuid"),
                            Field("distribution_uuid"),
                            migrate = True,
                            fake_migrate = False,
                            )
            bkp_table = db[bkp_tablename]
            cleanup = True

            left = pftable.on(pftable.id == ndtable.filter_id)
            query = (ndtable.filter_id != None) & (ndtable.deleted == False)
            rows = db(query).select(ndtable.uuid, pftable.uuid, left=left)

            saved = 0
            for row in rows:
                dist, fltr = row[ndtable], row[pftable]
                # Skip broken joins
                if not dist or not fltr:
                    info("-")
                    continue

                bkp_table.update_or_insert(filter_uuid=fltr.uuid,
                                           distribution_uuid=dist.uuid,
                                           )
                saved += 1
                info(".")

            if cleanup:
                db._adapter._drop_table_cleanup(bkp_table)
            infoln("...done (%s links saved)" % saved)
        else:
            infoln("...failed - backup table exists")
            failed = True
    else:
        infoln("...failed - incompatible data model")
        failed = True

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
