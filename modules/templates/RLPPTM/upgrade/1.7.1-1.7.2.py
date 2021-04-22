# -*- coding: utf-8 -*-
#
# Database upgrade script
#
# RLPPTM Template Version 1.7.1 => 1.7.2
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/RLPPTM/upgrade/1.7.1-1.7.2.py
#
import sys

#from gluon.storage import Storage
#from gluon.tools import callback

from s3 import S3Duplicate

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
ltable = s3db.org_service_site

IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "RLPPTM")

# -----------------------------------------------------------------------------
# Restore site service links (NB this must be the first step)
#
if not failed:
    info("Restore site services")

    s3db.table("org_service")
    s3db.table("org_site")

    # Pick up the backup table
    try:
        db.define_table("org_service_site_old",
                        Field("service_id", "reference org_service"),
                        Field("site_id", "reference org_site"),
                        migrate = False,
                        )
        otable = db.org_service_site_old
        query = (otable.id > 0)
        rows = db(otable.id>0).select(otable.service_id,
                                    otable.site_id,
                                    )
    except:
        # Backup table doesn't exist
        infoln("...skipped (backup table not found, did you execute prep-1.7.2?)")
        db.rollback()
    else:
        # Restore the links
        ltable.truncate()
        restored = 0
        seen = set()
        for row in rows:
            service_id = row.service_id
            site_id = row.site_id
            if (service_id, site_id) in seen:
                continue
            else:
                restored += 1
                seen.add((service_id, site_id))
                ltable.insert(service_id = row.service_id,
                              site_id = row.site_id,
                              )
        otable.drop()
        infoln("...done (%s links restored)" % restored)

# -----------------------------------------------------------------------------
# Deploy new CMS items
#
if not failed:
    info("Deploy new CMS items")

    # File and Stylesheet Paths
    stylesheet = os.path.join(IMPORT_XSLT_FOLDER, "cms", "post.xsl")
    filename = os.path.join(TEMPLATE_FOLDER, "cms_post.csv")

    # Only import relevant CMS posts, do not update any existing ones
    def cms_post_duplicate(item):
        name = item.data.get("name")
        if name in ("SiteServiceIntro",
                    ):
            S3Duplicate(noupdate=True)(item)
        else:
            item.skip = True

    # Import, fail on any errors
    try:
        with open(filename, "r") as File:
            resource = s3db.resource("cms_post")
            resource.configure(deduplicate = cms_post_duplicate)
            resource.import_xml(File,
                                format = "csv",
                                stylesheet = stylesheet,
                                )
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
