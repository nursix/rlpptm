# -*- coding: utf-8 -*-
#
# Database upgrade script
#
# RLPPTM Template Version 1.9.3 => 1.10.0
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/RLPPTM/upgrade/1.9.3-1.10.0.py
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
rtable = s3db.disease_testing_report
ftable = s3db.org_facility

IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "RLPPTM")

# -----------------------------------------------------------------------------
# Generate facility IDs
#
if not failed:
    info("Generate facility IDs")

    from templates.RLPPTM.helpers import set_facility_code

    updated = 0

    query = (ftable.deleted == False)
    rows = db(query).select(ftable.id)
    for row in rows:
        code = set_facility_code(row.id)
        if code:
            info(".")
            updated += 1
    infoln("...done (%s facilities updated)" % updated)

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
        if name in ("TestResultRegistrationIntroDisabled",
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
# Deploy new processing types
#
if not failed:
    info("Deploy new processing types")

    # File and Stylesheet Paths
    stylesheet = os.path.join(IMPORT_XSLT_FOLDER, "auth", "processing_type.xsl")
    filename = os.path.join(TEMPLATE_FOLDER, "auth_processing_type.csv")

    # Only import relevant items
    def auth_processing_type_duplicate(item):
        code = item.data.get("code")
        if code in ("CWA_ANONYMOUS",
                    "CWA_PERSONAL"
                    ):
            S3Duplicate(primary=("code",), noupdate=True)(item)
        else:
            item.skip = True

    # Import, fail on any errors
    try:
        with open(filename, "r") as File:
            resource = s3db.resource("auth_processing_type")
            resource.configure(deduplicate=auth_processing_type_duplicate)
            resource.import_xml(File, format="csv", stylesheet=stylesheet)
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
# Deploy new consent options
#
if not failed:
    info("Deploy new consent options")

    # File and Stylesheet Paths
    stylesheet = os.path.join(IMPORT_XSLT_FOLDER, "auth", "consent_option.xsl")
    filename = os.path.join(TEMPLATE_FOLDER, "auth_consent_option.csv")

    # Import only relevant items
    def auth_consent_option_duplicate(item):
        name = item.data.get("name")
        if name in ("Einwilligung für anonyme CWA-Meldung",
                    "Einwilligung für namentliche CWA-Meldung",
                    ):
            S3Duplicate(primary=("type_id",), noupdate=True)(item)
        else:
            item.skip = True

    # Import, fail on any errors
    try:
        with open(filename, "r") as File:
            resource = s3db.resource("auth_consent_option")
            resource.configure(deduplicate=auth_consent_option_duplicate)
            resource.import_xml(File, format="csv", stylesheet=stylesheet)
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
# Fix ownership for daily reports
#
if not failed:
    info("Fix ownership of daily reports")

    query = (rtable.deleted == False)
    auth.set_realm_entity(rtable, query, force_update=True)
    infoln("...done")

# -----------------------------------------------------------------------------
# Upgrade user roles
#
if not failed:
    info("Upgrade user roles")

    bi = s3base.S3BulkImporter()
    filename = os.path.join(TEMPLATE_FOLDER, "auth_roles.csv")

    with open(filename, "r") as File:
        try:
            bi.import_role(filename)
        except Exception as e:
            infoln("...failed")
            infoln(sys.exc_info()[1])
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
