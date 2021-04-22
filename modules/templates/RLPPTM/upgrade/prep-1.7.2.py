# -*- coding: utf-8 -*-
#
# Database upgrade script
#
# RLPPTM Template Version 1.7.1
#
# Execute in web2py folder before code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/RLPPTM/upgrade/prep-1.7.2.py
#
import os

db.executesql("ALTER TABLE org_service_site RENAME TO org_service_site_old;")
db.commit();

dbt = os.path.join(current.request.folder, "databases", "%s_org_service_site.table" % db._uri_hash)
if os.path.exists(dbt):
    os.unlink(dbt)
