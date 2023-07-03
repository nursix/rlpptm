# Database upgrade script
#
# RLPPTM Template Version 1.21.0 => 1.21.1
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/RLPPTM/upgrade/1.21.0-1.21.1.py
#
import sys

#from core import S3Duplicate
from templates.RLPPTM.models.org import TestProvider

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
#rtable = s3db.org_representative
dtable = s3db.doc_document
vtable = s3db.org_verification
ftable = s3db.org_facility

# Paths
IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "RLPPTM")

# -----------------------------------------------------------------------------
# Set default status for all documents
#
if not failed:
    info("Set default document status")

    # All existing documents are released
    updated = db(dtable.status == None).update(status="RELEASED",
                                               modified_on = dtable.modified_on,
                                               modified_by = dtable.modified_by,
                                               )
    if updated is None:
        infoln("...failed")
        failed = True
    else:
        infoln("...done (%s documents updated)" % updated)

# -----------------------------------------------------------------------------
# Update ownership for organisation documents
#
if not failed:
    info("Update ownership for organisation documents")

    query = (dtable.doc_id == None) & \
            (dtable.organisation_id != None) & \
            (dtable.status != "EVIDENCE") & \
            (dtable.deleted == False)

    ORG_ADMIN = auth.get_system_roles().ORG_ADMIN

    updated = db(query).update(owned_by_user = dtable.created_by,
                               owned_by_group = ORG_ADMIN,
                               modified_on = dtable.modified_on,
                               modified_by = dtable.modified_by,
                               )

    if updated is None:
        infoln("...failed")
        failed = True
    else:
        infoln("...done (%s documents updated)" % updated)

# -----------------------------------------------------------------------------
# Update ownership for facility documents
#
if not failed:
    info("Update ownership for facility documents")

    join = ftable.on(ftable.doc_id == dtable.doc_id)
    query = (dtable.status != "EVIDENCE") & \
            (dtable.deleted == False)
    facility_documents = db(query)._select(dtable.id, join=join)

    ORG_ADMIN = auth.get_system_roles().ORG_ADMIN

    query = dtable.id.belongs(facility_documents)
    updated = db(query).update(owned_by_user = dtable.created_by,
                               owned_by_group = ORG_ADMIN,
                               modified_on = dtable.modified_on,
                               modified_by = dtable.modified_by,
                               )

    if updated is None:
        infoln("...failed")
        failed = True
    else:
        infoln("...done (%s documents updated)" % updated)

# -----------------------------------------------------------------------------
# Update context links for facility documents
#
if not failed:
    info("Update context links in facility documents")

    join = ftable.on(ftable.doc_id == dtable.doc_id)
    query = (dtable.deleted == False)
    rows = db(query).select(dtable.id,
                            ftable.organisation_id,
                            ftable.site_id,
                            join = join,
                            )
    updated = 0
    for row in rows:
        document = row.doc_document
        facility = row.org_facility
        document.update_record(organisation_id = facility.organisation_id,
                               site_id = facility.site_id,
                               modified_on = dtable.modified_on,
                               modified_by = dtable.modified_by,
                               )
        updated += 1

    infoln("...done (%s documents updated)" % updated)

# -----------------------------------------------------------------------------
# Fix document realms
#
if not failed:
    info("Fix document realms")

    query = (dtable.deleted == False)
    auth.set_realm_entity(dtable, query, force_update=True)

    infoln("...done")

# -----------------------------------------------------------------------------
# Generate org_audit record for all providers
#
if not failed:
    info("Add audit records for test providers...")

    query = (vtable.deleted == False)
    rows = db(query).select(vtable.organisation_id,
                            groupby = vtable.organisation_id,
                            )
    created = 0
    for row in rows:
        provider = TestProvider(row.organisation_id)
        if provider.add_audit_status():
            provider.update_audit_status()
            created += 1
            info("+")
        else:
            info(".")

    infoln("...done (%s status records created)" % created)

# -----------------------------------------------------------------------------
# Upgrade user roles
#
if not failed:
    info("Upgrade user roles")

    bi = s3base.BulkImporter()
    filename = os.path.join(TEMPLATE_FOLDER, "auth_roles.csv")

    try:
        error = bi.import_roles(filename)
    except Exception as e:
        error = sys.exc_info()[1] or "unknown error"
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
