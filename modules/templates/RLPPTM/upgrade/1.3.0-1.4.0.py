# -*- coding: utf-8 -*-
#
# Database upgrade script
#
# RLPPTM Template Version 1.3.0 => 1.4.0
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/RLPPTM/upgrade/1.3.0-1.4.0.py
#
#import datetime
import sys
from s3 import S3Duplicate

#from gluon.storage import Storage
#from gluon.tools import callback

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
gtable = s3db.org_group

IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "RLPPTM")

# -----------------------------------------------------------------------------
# Deploy new projects incl. codes and tags
#
if not failed:
    info("Install/update projects")

    # Import new templates
    stylesheet = os.path.join(IMPORT_XSLT_FOLDER, "project", "project.xsl")
    filename = os.path.join(TEMPLATE_FOLDER, "project_project.csv")

    # Import, fail on any errors
    try:
        with open(filename, "r") as File:
            resource = s3db.resource("project_project")
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
# Add all existing test stations to the original project
#
if not failed:
    info("Link all test stations to the original project")

    from templates.RLPPTM.config import TESTSTATIONS

    gtable = s3db.org_group
    mtable = s3db.org_group_membership
    ltable = s3db.project_organisation
    ptable = s3db.project_project

    query = (ptable.name == "COVID-19 Tests für Schulpersonal") & \
            (ptable.deleted == False)
    project = db(query).select(ptable.id,
                               limitby = (0, 1),
                               ).first()
    if project:
        project_id = project.id

        join = gtable.on((gtable.id == mtable.group_id) & \
                        (gtable.name == TESTSTATIONS) & \
                        (gtable.deleted == False))
        query = (mtable.deleted == False)
        rows = db(query).select(mtable.organisation_id,
                                groupby = mtable.organisation_id,
                                join = join,
                                )
        updated = 0
        for row in rows:
            organisation_id = row.organisation_id
            # Only link those organisations which are not yet linked to any project
            query = (ltable.organisation_id == organisation_id) & \
                    (ltable.deleted == False)
            existing = db(query).select(ltable.id, limitby=(0, 1)).first()
            if existing:
                continue
            link = {"project_id": project_id,
                    "organisation_id": organisation_id,
                    "role": 2,
                    }
            try:
                link["id"] = ltable.insert(**link)
                auth.s3_set_record_owner(ltable, link)
                s3db.onaccept(ltable, link, method="create")
            except:
                infoln("...failed")
                infoln(sys.exc_info()[1])
                failed = True
                break
            else:
                updated += 1
        infoln("...done (%s records updated)" % updated)
    else:
        infoln("...failed (project not found)")
        failed = True

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
        if name in ("ProjectParticipationIntro"):
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
