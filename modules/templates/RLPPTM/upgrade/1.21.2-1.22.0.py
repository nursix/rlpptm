# Database upgrade script
#
# RLPPTM Template Version 1.21.2 => 1.22.0
#
# Run after code upgrade like:
# edenctl run applications/eden/modules/templates/RLPPTM/upgrade/1.21.2-1.22.0.py
#
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
sitable = s3db.supply_item
sptable = s3db.supply_item_pack
ndtable = s3db.cms_newsletter_distribution

# Paths
IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "RLPPTM")

settings.base.debug = True

# -----------------------------------------------------------------------------
# Migrate saved filters
#
if not failed:
    info("Migrate saved filters")

    pftable = None
    skip, cleanup = False, False

    if not skip:
        uftable = s3db.table("usr_filter")
        if not uftable:
            infoln("...target table missing, skipping")

    if not skip:
        pftable = s3db.table("pr_filter")
        if not pftable:
            db.define_table("pr_filter",
                            s3db.super_link("pe_id", "pr_pentity"),
                            Field("title"),
                            Field("controller"),
                            Field("function"),
                            Field("resource"),
                            Field("url"),
                            Field("description", "text"),
                            Field("query", "text"),
                            Field("serverside", "json"),
                            Field("comments", "text"),
                            *MetaFields(),
                            migrate = True,
                            fake_migrate = True,
                            )
            pftable = db.pr_filter
            cleanup = True

    if not skip:

        rows, migrated = [], 0

        left = uftable.on(uftable.uuid == pftable.uuid)
        query = (pftable.id > 0) & (uftable.id == None)
        try:
            rows = db(query).select(pftable.ALL, left=left, orderby=pftable.id)
        except Exception:
            infoln("...failed: legacy table not found or incompatible model")
            failed = True

    if not failed and not skip:
        # Rewrite pr_filter rows as usr_filter
        for row in rows:
            record = {fn:row[fn] for fn in uftable.fields if fn in row and fn != "id"}
            saved_filter_id = uftable.insert(**record)
            migrated += 1
            info(".")
        infoln("...done (%s/%s filters migrated)" % (migrated, len(rows)))

    if cleanup and pftable:
        db._adapter._drop_table_cleanup(pftable)

# -----------------------------------------------------------------------------
# Restore newsletter distribution filters
#
if not failed:
    info("Restore newsletter distribution filters")

    bkp_table = None
    skip, cleanup = False, False

    if not uftable or not ndtable:
        infoln("...one or more target tables missing, skipping")
        skip = True

    if not skip:
        bkp_tablename = "cms_newsletter_distribution_backup"
        bkp_table = s3db.table(bkp_tablename)
        if not bkp_table:
            # Temporarily define cms_newsletter_distribution_backup
            db.define_table(bkp_tablename,
                            Field("filter_uuid"),
                            Field("distribution_uuid"),
                            migrate = True,
                            fake_migrate = True,
                            )
            bkp_table = db[bkp_tablename]
            cleanup = True

    rows, fixed = [], 0
    if not skip:
        left = uftable.on(uftable.uuid == bkp_table.filter_uuid)
        query = (ndtable.uuid == bkp_table.distribution_uuid) & \
                (ndtable.saved_filter_id == None) & \
                (ndtable.deleted == False) & \
                (uftable.id != None)
        try:
            rows = db(query).select(ndtable.id, uftable.id, left=left)
        except Exception:
            infoln("...failed: backup table not found or incompatible model")
            failed = True

    if not failed and not skip:
        # Restore links
        for row in rows:
            dist, fltr = row[ndtable], row[uftable]
            dist.update_record(saved_filter_id=fltr.id,
                               modified_on = ndtable.modified_on,
                               modified_by = ndtable.modified_by,
                               )
            fixed += 1
            info(".")
        # Remove orphaned distribution records
        query = (ndtable.saved_filter_id == None) & \
                (ndtable.deleted == False)
        removed = db(query).delete()
        infoln("...done (%s/%s links restored, %s orphaned links removed)" % (fixed, len(rows), removed))

    if cleanup and bkp_table:
        db._adapter._drop_table_cleanup(bkp_table)

# -----------------------------------------------------------------------------
# Migrate supply items
#
if not failed:
    info("Fix invalid units of measure")

    um_map = {"10 Liter": ("L", 10)}
    updated, fixed = 0, 0

    for unit, correction in um_map.items():
        unit_code, factor = correction

        query = (sitable.um == unit) & (sitable.deleted == False)
        items = db(query).select(sitable.id)
        item_ids = {item.id for item in items}

        updated += db(query).update(um = unit_code,
                                    modified_on = sitable.modified_on,
                                    modified_by = sitable.modified_by,
                                    )

        query = (sptable.item_id.belongs(item_ids)) & (sptable.deleted == False)

        fixed += db(query).update(quantity = sptable.quantity*factor,
                                  modified_on = sptable.modified_on,
                                  modified_by = sptable.modified_by,
                                  )

    infoln("...done (%s units updated, %s pack quantities fixed)" % (updated, fixed))

if not failed:
    info("Map units of measure to unit codes...")

    # Map old free-text units of measure to new unit codes
    units_map = {"pc": "pc",
                 "piece": "pc",
                 "Piece": "pc",
                 "Stück": "pc",
                 "Stueck": "pc",

                 "pair": "pair",
                 "set": "set",
                 "mg": "mg",
                 "g": "g",
                 "kg": "kg",
                 "m": "m",
                 "ml": "ml",

                 "L": "L",
                 "l": "L",
                 "Liter": "L",
                 "liter": "L",
                 "10 Liter": "L",

                 "btl": "btl",
                 "Flasche": "btl",
                 "Bottle": "btl",
                 "bottle": "btl",

                 "pkg": "pkg",
                 "Paket": "pkg",
                 "Package": "pkg",
                 "package": "pkg",
                 }

    unmapped = []

    updated, skipped = 0, 0
    items = db(sitable.deleted == False).select(sitable.id, sitable.um)
    for item in items:
        unit_code = units_map.get(item.um)
        if not unit_code:
            unmapped.append(item.um)
            info("?")
        elif item.um != unit_code:
            item.update_record(um = unit_code,
                               modified_on = sitable.modified_on,
                               modified_by = sitable.modified_by,
                               )
            updated += 1
            info("+")
        else:
            skipped += 1
            info(".")

    if unmapped:
        infoln("...failed, missing mapping for %s" ",".join(['"%s"' % u for u in unmapped]))
        failed = True
    else:
        infoln("...done (%s items ok, %s items updated)" % (skipped, updated))

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
