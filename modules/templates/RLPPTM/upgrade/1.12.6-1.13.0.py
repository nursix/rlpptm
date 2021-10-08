# -*- coding: utf-8 -*-
#
# Database upgrade script
#
# RLPPTM Template Version 1.12.6 => 1.13.0
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/RLPPTM/upgrade/1.12.6-1.13.0.py
#
import sys

#from gluon.storage import Storage
#from gluon.tools import callback
from core import S3Duplicate

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
dtable = s3db.disease_demographic
ltable = s3db.disease_testing_demographic

IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "RLPPTM")

# -----------------------------------------------------------------------------
# Deploy disease demographics
#
if not failed:
    info("Deploy disease demographics")

    # Import new templates
    stylesheet = os.path.join(IMPORT_XSLT_FOLDER, "disease", "demographic.xsl")
    filename = os.path.join(TEMPLATE_FOLDER, "disease_demographic.csv")

    # Import, fail on any errors
    try:
        with open(filename, "r") as File:
            resource = s3db.resource("disease_demographic")
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
# Generate default demographic subtotals for existing testing reports
#
if not failed:
    info("Generate default demographic subtotals for existing testing reports")

    default = "UNSPEC"

    # Look up the default demographic
    query = (dtable.code == default) & \
            (dtable.deleted == False)
    row = db(query).select(dtable.id, limitby=(0, 1)).first()
    if row:

        demographic_id = row.id

        # Lookup all disease_testing_report without a corresponding disease_testing_demographic
        left = ltable.on((ltable.report_id == rtable.id) & \
                        (ltable.deleted == False))
        query = (rtable.deleted == False) & \
                (ltable.id == None)
        reports = db(query).select(rtable.id,
                                   rtable.tests_total,
                                   rtable.tests_positive,
                                   left = left,
                                   )
        if reports:
            info("...%s reports to fix..." % len(reports))
            added = 0
            set_record_owner = auth.s3_set_record_owner
            for report in reports:
                subtotal = {"report_id": report.id,
                            "demographic_id": demographic_id,
                            "tests_total": report.tests_total,
                            "tests_positive": report.tests_positive,
                             }
                subtotal_id = ltable.insert(**subtotal)
                set_record_owner(ltable, subtotal_id)
                info("+")
                added += 1
            infoln("...done (%s subtotals added)" % added)
        else:
            infoln("...done (nothing to fix)")
    else:
        infoln("...failed (default demographic not found)")
        failed = True

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
        if name in ("Subject FacilityObsolete",
                    "Message FacilityObsolete",
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
# Cleanup public test station registry
#
#if not failed:
#    info("Cleaning up public test stations registry")
#
#    from templates.RLPPTM.maintenance import Daily
#
#    try:
#        errors = Daily.cleanup_public_registry()
#    except Exception as e:
#        infoln("...failed")
#        infoln(sys.exc_info()[1])
#        failed = True
#    else:
#        if errors:
#            sys.stderr.write("\n%s\n" % errors)
#        infoln("...done")
#
# -----------------------------------------------------------------------------
# Finishing up
#
if failed:
    db.rollback()
    infoln("UPGRADE FAILED - Action rolled back.")
else:
    db.commit()
    infoln("UPGRADE SUCCESSFUL.")
