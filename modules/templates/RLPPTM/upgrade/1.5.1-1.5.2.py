# -*- coding: utf-8 -*-
#
# Database upgrade script
#
# RLPPTM Template Version 1.5.1 => 1.5.2
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/RLPPTM/upgrade/1.5.1-1.5.2.py
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
dtable = s3db.fin_voucher_debit

IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "RLPPTM")

# -----------------------------------------------------------------------------
# Set cancelled-Flag for all debits to False
#
if not failed:
    info("Upgrade voucher debits")

    query = (dtable.cancelled == None)
    updated = db(query).update(cancelled = False)

    infoln("...done (%s items updated)" % updated)

# -----------------------------------------------------------------------------
# Finishing up
#
if failed:
    db.rollback()
    infoln("UPGRADE FAILED - Action rolled back.")
else:
    db.commit()
    infoln("UPGRADE SUCCESSFUL.")
