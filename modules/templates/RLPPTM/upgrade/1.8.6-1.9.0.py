# -*- coding: utf-8 -*-
#
# Database upgrade script
#
# RLPPTM Template Version 1.8.6 => 1.9.0
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/RLPPTM/upgrade/1.8.6-1.9.0.py
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
# Clean up duplicate CMS items
#
if not failed:
    info("Cleanup duplicate CMS items")

    # Find all CMS items that are
    ctable = s3db.cms_post
    ltable = s3db.cms_post_module

    left = ltable.on((ltable.post_id == ctable.id) &
                     (ltable.deleted == False))
    query = (ctable.series_id == None) & \
            (ctable.deleted == False) & \
            (ltable.id == None)
    rows = db(query).select(ctable.id,
                            ctable.name,
                            left = left,
                            )
    removed = 0
    for row in rows:
        # Check if there is a name duplicate that is linked
        query = (ctable.name == row.name) & \
                (ctable.series_id == None) & \
                (ctable.deleted == False)
        duplicate = db(query).select(ctable.id,
                                     join = left,
                                     limitby = (0, 1),
                                     ).first()
        if duplicate:
            info(".")
            row.delete_record()
            removed += 1
    infoln("...done (%s items removed)" % removed)

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
        if name in ("Subject FacilityApproved - Disabled",
                    "Message FacilityApproved",
                    "Subject FacilityReview - Disabled",
                    "Message FacilityReview",
                    "FacilityMPAVRequirements",
                    "FacilityHygienePlanRequirements",
                    "FacilityLayoutRequirements",
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
