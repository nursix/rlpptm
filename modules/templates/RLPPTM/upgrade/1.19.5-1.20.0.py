# Database upgrade script
#
# RLPPTM Template Version 1.19.5 => 1.20.0
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/RLPPTM/upgrade/1.19.5-1.20.0.py
#
import sys

from core import S3Duplicate
from templates.RLPPTM.models.org import TestProvider
from templates.RLPPTM.helpers import is_org_group
from templates.RLPPTM.config import TESTSTATIONS
from templates.RLPPTM.models.org import ProviderRepresentative

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
#otable = s3db.org_organisation
rqtable = s3db.org_requirements
rtable = s3db.org_representative
htable = s3db.hrm_human_resource
ttable = s3db.hrm_human_resource_tag

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
        if name in ("OrgContactIntro",
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
# Update provider requirements: rinforeq=minforeq
#
if not failed:
    info("Update provider requirements")

    updated = db(rqtable.id>0).update(rinforeq=rqtable.minforeq)

    infoln("...done (%s records updated)" % updated)

# -----------------------------------------------------------------------------
# Generate representative records
#
if not failed:
    info("Generate representative verifications")

    scp = ttable.with_alias("scp")
    crc = ttable.with_alias("crc")
    reg = ttable.with_alias("regform")

    left = [scp.on((scp.human_resource_id == htable.id) & \
                   (scp.tag == "SCP") & \
                   (scp.deleted == False)),
            crc.on((crc.human_resource_id == htable.id) & \
                   (crc.tag == "CRC") & \
                   (crc.deleted == False)),
            reg.on((reg.human_resource_id == htable.id) & \
                   (reg.tag == "REGFORM") & \
                   (reg.deleted == False)),
            ]

    query = (htable.deleted == False) & \
            ((scp.id != None) | (crc.id != None) | (reg.id != None))
    rows = db(query).select(htable.id,
                            htable.modified_on,
                            htable.person_id,
                            htable.organisation_id,
                            htable.org_contact,
                            htable.status,
                            scp.id,
                            scp.created_on,
                            scp.modified_on,
                            scp.value,
                            crc.id,
                            crc.created_on,
                            crc.modified_on,
                            crc.value,
                            reg.id,
                            reg.created_on,
                            reg.modified_on,
                            reg.value,
                            left=left,
                            )
    info("...[%s staff record(s)]..." % len(rows))

    organisations = set()
    generated, approved = 0, 0
    for row in rows:

        hr = row.hrm_human_resource
        person_id = hr.person_id
        organisation_id = hr.organisation_id

        organisations.add(organisation_id)

        crc_tag = row.crc
        scp_tag = row.scp
        reg_tag = row.regform

        # Check if org_representative exists
        query = (rtable.person_id == person_id) & \
                (rtable.organisation_id == organisation_id) & \
                (rtable.deleted == False)
        record = db(query).select(rtable.id, limitby=(0, 1)).first()
        if record:
            info("x")
            continue

        # generate org_representative
        representative = {"person_id": person_id,
                          "organisation_id": organisation_id,
                          }

        # set start date to oldest TAG created_on
        dates = [tag.created_on for tag in (crc_tag, scp_tag, reg_tag) if tag.id]
        start = representative["date"] = min(dates)

        # check data + set status flags
        record = Storage(person_id = person_id,
                         person_data = None,
                         contact_data = None,
                         address_data = None,
                         user_account = None,
                         )
        update = {}
        accepted = ProviderRepresentative.check_data(record = record,
                                                     update = update,
                                                     show_errors = False,
                                                     )[0]
        representative.update(update)

        # set scp/crc/regform from tags
        values = {"N/A": "N/A", "APPROVED": "APPROVED", "REJECT": "REJECTED"}
        representative["scp"] = values.get(scp_tag.value, "N/A") if scp_tag.id else "N/A"
        representative["crc"] = values.get(crc_tag.value, "N/A") if crc_tag.id else "N/A"
        representative["regform"] = values.get(reg_tag.value, "N/A") if reg_tag.id else "N/A"

        # determine overall status
        tags = ("scp", "crc", "regform")
        if all(representative[tag] == "APPROVED" for tag in tags) and accepted:
            status = "APPROVED"
        else:
            status = "REVISE"
        representative["status"] = status

        # determine active
        active = representative["active"] = hr.org_contact and \
                                            hr.status == 1 and \
                                            status == "APPROVED"
        if not active:
            dates = [tag.modified_on for tag in (crc_tag, scp_tag, reg_tag) if tag.id]
            dates.extend([hr.modified_on, start])
            representative["end_date"] = max(dates)

        # Create new record
        representative_id = representative["id"] = rtable.insert(**representative)

        # Postprocess new record
        s3db.update_super(rtable, representative)
        current.auth.s3_set_record_owner(rtable, representative_id)
        s3db.onaccept(rtable, representative, method="create")

        # Set verification hash if approved
        if status == "APPROVED":
            rep = ProviderRepresentative(representative_id)
            vhash = rep.vhash()[1]
            if vhash:
                rep.record.update_record(dhash=vhash)

        generated += 1
        if status == "APPROVED":
            info("+")
            approved += 1
        else:
            info("-")

    infoln("...done (%s verification(s) generated)" % generated)

# -----------------------------------------------------------------------------
# Set realm entity for org_verification
#
if not failed:
    info("Update provider verifications")

    vtable = s3db.org_verification

    auth.set_realm_entity(vtable, vtable.deleted>0, force_update=True)
    info("...")

    if organisations:
        updated = 0
        for organisation_id in organisations:
            if is_org_group(organisation_id, TESTSTATIONS):
                provider = TestProvider(organisation_id)
                provider.update_verification()
                info("*")
                updated += 1
        infoln("...done (%s verifications updated)" % updated)
    else:
        infoln("...skip")

# -----------------------------------------------------------------------------
# Fix upload-date for documents
#
if not failed:
    info("Fix upload dates for documents")

    dtable = s3db.doc_document

    query = (dtable.date == None)
    updated = db(query).update(date=dtable.created_on)

    infoln("...done (%s records updated)" % updated)

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
