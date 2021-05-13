# -*- coding: utf-8 -*-
#
# Database upgrade script
#
# RLPPTM Template Version 1.8.4 => 1.8.5
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/RLPPTM/upgrade/1.8.4-1.8.5.py
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
ftable = s3db.org_facility
ttable = s3db.org_site_tag

IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "RLPPTM")

# -----------------------------------------------------------------------------
# Add workflow tags to all facilities
#
if not failed:
    info("Add new workflow tags")

    WORKFLOW = ("STATUS", "MPAV", "HYGIENE", "LAYOUT")

    left = ttable.on((ttable.site_id == ftable.site_id) & \
                     (ttable.tag == "PUBLIC") & \
                     (ttable.deleted == False))
    query = (ftable.deleted == False)
    rows = db(query).select(ftable.site_id,
                            ttable.id,
                            ttable.value,
                            left = left,
                            )

    added = 0
    for row in rows:
        site = row.org_facility
        public = row.org_site_tag

        if public.id is None:
            # Add PUBLIC-tag
            is_public = False
            tag = {"site_id": site.site_id,
                   "tag": "PUBLIC",
                   "value": "N",
                   }
            ttable.insert(**tag)
            added += 1
        else:
            is_public = public.value == "Y"

        for tagname in WORKFLOW:
            query = (ttable.site_id == site.site_id) & \
                    (ttable.tag == tagname) & \
                    (ttable.deleted == False)
            if not db(query).select(ttable.id, limitby=(0, 1)).first():
                tag = {"site_id": site.site_id,
                       "tag": tagname,
                       "value": "APPROVED" if is_public else "REVIEW",
                       }
                ttable.insert(**tag)
                added += 1
        info(".")

    infoln("...done (%s tags added)" % added)

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
        if name in ("SiteDocumentsIntro",
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
