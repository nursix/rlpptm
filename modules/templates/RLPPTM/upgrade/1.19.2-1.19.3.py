# Database upgrade script
#
# RLPPTM Template Version 1.19.2 => 1.19.3
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/RLPPTM/upgrade/1.19.2-1.19.3.py
#
import sys

from core import S3Duplicate
from templates.RLPPTM.config import TESTSTATIONS
from templates.RLPPTM.models.org import TestProvider

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
#otable = s3db.org_organisation

# Paths
IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "RLPPTM")

# -----------------------------------------------------------------------------
# Deploy new CMS items
#
if not failed:
    info("Deploy new CMS items")

    resource = s3db.resource("cms_post")

    # File and stylesheet paths
    stylesheet = os.path.join(IMPORT_XSLT_FOLDER, "cms", "post.xsl")
    filename = os.path.join(TEMPLATE_FOLDER, "cms_post.csv")

    # Only import relevant CMS posts, do not update existing ones
    def cms_post_duplicate(item):
        name = item.data.get("name")
        if name in ("CommissionYYYYMMDD",
                    ):
            S3Duplicate(noupdate=True)(item)
        else:
            item.skip = True
    resource.configure(deduplicate = cms_post_duplicate)

    # Import, capture errors
    try:
        with open(filename, "r") as File:
            resource.import_xml(File,
                                source_type = "csv",
                                stylesheet = stylesheet,
                                )
    except Exception as e:
        error = sys.exc_info()[1] or "unknown error"
    else:
        error = resource.error

    # Fail on any error
    if error:
        infoln("...failed")
        infoln(error)
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

# END =========================================================================
