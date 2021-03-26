# -*- coding: utf-8 -*-

from collections import OrderedDict

from gluon import current
from gluon.storage import Storage

def config(settings):
    """
        Cumbria Emergency Assistance Centres
    """

    T = current.T

    settings.base.system_name = T("Cumbria Emergency Assistance Centres")
    settings.base.system_name_short = T("EAC")

    # PrePopulate data
    settings.base.prepopulate += ("CumbriaEAC",)
    settings.base.prepopulate_demo += ("CumbriaEAC/Demo",)

    # Theme (folder to use for views/layout.html)
    settings.base.theme = "CCC"
    # Custom Logo
    #settings.ui.menu_logo = "/%s/static/themes/CumbriaEAC/img/logo.png" % current.request.application

    # Authentication settings
    # Should users be allowed to register themselves?
    settings.security.self_registration = False
    # Do new users need to verify their email address?
    #settings.auth.registration_requires_verification = True
    # Do new users need to be approved by an administrator prior to being able to login?
    #settings.auth.registration_requires_approval = True
    #settings.auth.registration_requests_organisation = True
    # Required for access to default realm permissions
    #settings.auth.registration_link_user_to = ["staff"]
    #settings.auth.registration_link_user_to_default = ["staff"]

    # Consent Tracking
    settings.auth.consent_tracking = True

    # Approval emails get sent to all admins
    settings.mail.approver = "ADMIN"

    # Restrict the Location Selector to just certain countries
    # NB This can also be over-ridden for specific contexts later
    # e.g. Activities filtered to those of parent Project
    #settings.gis.countries = ("US",)
    # Uncomment to display the Map Legend as a floating DIV, so that it is visible on Summary Map
    settings.gis.legend = "float"
    # Uncomment to Disable the Postcode selector in the LocationSelector
    #settings.gis.postcode_selector = False # @ToDo: Vary by country (include in the gis_config!)
    # Uncomment to show the Print control:
    # http://eden.sahanafoundation.org/wiki/UserGuidelines/Admin/MapPrinting
    #settings.gis.print_button = True

    # Use GetAddress.io to lookup Addresses from Postcode
    settings.gis.postcode_to_address = "getaddress"

    # -------------------------------------------------------------------------
    # L10n (Localization) settings
    settings.L10n.languages = OrderedDict([
        ("en-gb", "English"),
    ])
    # Default Language
    settings.L10n.default_language = "en-gb"
    # Uncomment to Hide the language toolbar
    settings.L10n.display_toolbar = False

    # Number formats (defaults to ISO 31-0)
    # Decimal separator for numbers (defaults to ,)
    settings.L10n.decimal_separator = "."
    # Thousands separator for numbers (defaults to space)
    settings.L10n.thousands_separator = ","

    # Security Policy
    # http://eden.sahanafoundation.org/wiki/S3AAA#System-widePolicy
    # 1: Simple (default): Global as Reader, Authenticated as Editor
    # 2: Editor role required for Update/Delete, unless record owned by session
    # 3: Apply Controller ACLs
    # 4: Apply both Controller & Function ACLs
    # 5: Apply Controller, Function & Table ACLs
    # 6: Apply Controller, Function, Table ACLs and Entity Realm
    # 7: Apply Controller, Function, Table ACLs and Entity Realm + Hierarchy
    # 8: Apply Controller, Function, Table ACLs, Entity Realm + Hierarchy and Delegations

    settings.security.policy = 5 # Controller, Function & Table ACLs

    # -------------------------------------------------------------------------
    # Comment/uncomment modules here to disable/enable them
    # Modules menu is defined in modules/eden/menu.py
    settings.modules = OrderedDict([
        # Core modules which shouldn't be disabled
        ("default", Storage(
            name_nice = T("Home"),
            restricted = False, # Use ACLs to control access to this module
            access = None,      # All Users (inc Anonymous) can see this module in the default menu & access the controller
            module_type = None  # This item is not shown in the menu
        )),
        ("admin", Storage(
            name_nice = T("Administration"),
            #description = "Site Administration",
            restricted = True,
            access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
            module_type = None  # This item is handled separately for the menu
        )),
        ("appadmin", Storage(
            name_nice = T("Administration"),
            #description = "Site Administration",
            restricted = True,
            module_type = None  # No Menu
        )),
        ("errors", Storage(
            name_nice = T("Ticket Viewer"),
            #description = "Needed for Breadcrumbs",
            restricted = False,
            module_type = None  # No Menu
        )),
        #("sync", Storage(
        #    name_nice = T("Synchronization"),
        #    #description = "Synchronization",
        #    restricted = True,
        #    access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
        #    module_type = None  # This item is handled separately for the menu
        #)),
        #("tour", Storage(
        #    name_nice = T("Guided Tour Functionality"),
        #    module_type = None,
        #)),
        #("translate", Storage(
        #    name_nice = T("Translation Functionality"),
        #    #description = "Selective translation of strings based on module.",
        #    module_type = None,
        #)),
        ("gis", Storage(
            name_nice = T("Map"),
            #description = "Situation Awareness & Geospatial Analysis",
            restricted = True,
            module_type = 6,     # 6th item in the menu
        )),
        ("pr", Storage(
            name_nice = T("Person Registry"),
            #description = "Central point to record details on People",
            restricted = True,
            access = "|1|",     # Only Administrators can see this module in the default menu (access to controller is possible to all still)
            module_type = 10
        )),
        ("org", Storage(
            name_nice = T("Organizations"),
            #description = 'Lists "who is doing what & where". Allows relief agencies to coordinate their activities',
            restricted = True,
            module_type = 1
        )),
        # HRM is required for access to default realm permissions
        ("hrm", Storage(
            name_nice = T("Staff"),
            #description = "Human Resources Management",
            restricted = True,
            module_type = 2,
        )),
        #("vol", Storage(
        #    name_nice = T("Volunteers"),
        #    #description = "Human Resources Management",
        #    restricted = True,
        #    module_type = 2,
        #)),
        ("cms", Storage(
          name_nice = T("Content Management"),
          #description = "Content Management System",
          restricted = True,
          module_type = 10,
        )),
        #("doc", Storage(
        #    name_nice = T("Documents"),
        #    #description = "A library of digital resources, such as photos, documents and reports",
        #    restricted = True,
        #    module_type = 10,
        #)),
        #("msg", Storage(
        #    name_nice = T("Messaging"),
        #    #description = "Sends & Receives Alerts via Email & SMS",
        #    restricted = True,
        #    # The user-visible functionality of this module isn't normally required. Rather it's main purpose is to be accessed from other modules.
        #    module_type = None,
        #)),
        #("supply", Storage(
        #    name_nice = T("Supply Chain Management"),
        #    #description = "Used within Inventory Management, Request Management and Asset Management",
        #    restricted = True,
        #    module_type = None, # Not displayed
        #)),
        #("inv", Storage(
        #    name_nice = T("Warehouses"),
        #    #description = "Receiving and Sending Items",
        #    restricted = True,
        #    module_type = 4
        #)),
        #("asset", Storage(
        #    name_nice = T("Assets"),
        #    #description = "Recording and Assigning Assets",
        #    restricted = True,
        #    module_type = 5,
        #)),
        # Vehicle depends on Assets
        #("vehicle", Storage(
        #    name_nice = T("Vehicles"),
        #    #description = "Manage Vehicles",
        #    restricted = True,
        #    module_type = 10,
        #)),
        #("req", Storage(
        #    name_nice = T("Requests"),
        #    #description = "Manage requests for supplies, assets, staff or other resources. Matches against Inventories where supplies are requested.",
        #    restricted = True,
        #    module_type = 10,
        #)),
        #("project", Storage(
        #    name_nice = T("Projects"),
        #    #description = "Tracking of Projects, Activities and Tasks",
        #    restricted = True,
        #    module_type = 2
        #)),
        ("cr", Storage(
            name_nice = T("Shelters"),
            #description = "Tracks the location, capacity and breakdown of victims in Shelters",
            restricted = True,
            module_type = 10
        )),
        #("hms", Storage(
        #    name_nice = T("Hospitals"),
        #    #description = "Helps to monitor status of hospitals",
        #    restricted = True,
        #    module_type = 10
        #)),
        #("br", Storage(
        #   name_nice = T("Beneficiary Registry"),
        #   #description = "Allow affected individuals & households to register to receive compensation and distributions",
        #   restricted = True,
        #   module_type = 10,
        #)),
        #("event", Storage(
        #    name_nice = T("Events"),
        #    #description = "Activate Events (e.g. from Scenario templates) for allocation of appropriate Resources (Human, Assets & Facilities).",
        #    restricted = True,
        #    module_type = 10,
        #)),
        #("transport", Storage(
        #   name_nice = T("Transport"),
        #   restricted = True,
        #   module_type = 10,
        #)),
        #("stats", Storage(
        #    name_nice = T("Statistics"),
        #    #description = "Manages statistics",
        #    restricted = True,
        #    module_type = None,
        #)),
    ])

    # -------------------------------------------------------------------------
    # Beneficiary Registry (Not Used)
    # Terminology to use when referring to cases (Beneficiary|Client|Case)
    #settings.br.case_terminology = "Client" # Evacuee
    # Disable assignment of cases to staff
    #settings.br.case_manager = False
    # Expose fields to track home address in case file
    #settings.br.case_address = True
    # Disable tracking of case activities
    #settings.br.case_activities = False
    # Disable tracking of individual assistance measures
    #settings.br.manage_assistance = False

    # -------------------------------------------------------------------------
    # Shelters
    # Uncomment to use a dynamic population estimation by calculations based on registrations
    settings.cr.shelter_population_dynamic = True

    cr_shelter_status_opts = {1 : T("Closed"),
                              #2 : T("Open##the_shelter_is"),
                              3 : T("Green"),
                              4 : T("Amber"),
                              5 : T("Red"),
                              }

    # -------------------------------------------------------------------------
    # Human Resources
    settings.hrm.org_required = False

    # -------------------------------------------------------------------------
    # Messaging
    settings.msg.require_international_phone_numbers = False

    # -------------------------------------------------------------------------
    # Persons
    settings.pr.hide_third_gender = False

    # -------------------------------------------------------------------------
    def eac_person_anonymize():
        """ Rules to anonymise a person """

        #auth = current.auth

        ANONYMOUS = "-"
        #anonymous_email = uuid4().hex

        title = "Name, Contacts, Address, Additional Information"

        rules = [{"name": "default",
                  "title": title,
                  "fields": {"first_name": ("set", ANONYMOUS),
                             "middle_name": ("set", ANONYMOUS),
                             "last_name": ("set", ANONYMOUS),
                             "pe_label": "remove",
                             #"date_of_birth": current.s3db.pr_person_obscure_dob,
                             "date_of_birth": "remove",
                             "comments": "remove",
                             },
                  "cascade": [("pr_contact", {"key": "pe_id",
                                              "match": "pe_id",
                                              "fields": {"contact_description": "remove",
                                                         "value": ("set", ""),
                                                         "comments": "remove",
                                                         },
                                              "delete": True,
                                              }),
                              ("pr_contact_emergency", {"key": "pe_id",
                                                        "match": "pe_id",
                                                        "fields": {"name": ("set", ANONYMOUS),
                                                                   "relationship": "remove",
                                                                   "phone": "remove",
                                                                   "comments": "remove",
                                                                   },
                                                        "delete": True,
                                                        }),
                              ("pr_address", {"key": "pe_id",
                                              "match": "pe_id",
                                              "fields": {"location_id": current.s3db.pr_address_anonymise,
                                                         "comments": "remove",
                                                         },
                                              }),
                              #("pr_person_details", {"key": "person_id",
                              #                       "match": "id",
                              #                       "fields": {"education": "remove",
                              #                                  "occupation": "remove",
                              #                                  },
                              #                       }),
                              ("pr_person_tag", {"key": "person_id",
                                                 "match": "id",
                                                 "fields": {"value": ("set", ANONYMOUS),
                                                            },
                                                 "delete": True,
                                                 }),
                              #("br_case", {"key": "person_id",
                              #             "match": "id",
                              #             "fields": {"comments": "remove",
                              #                        },
                              #             "cascade": [("br_note", {"key": "id",
                              #                                      "match": "case_id",
                              #                                      "fields": {"note": "remove",
                              #                                                 },
                              #                                      "delete": True,
                              #                                      }),
                              #                         ],
                              #             }),
                              ("hrm_human_resource", {"key": "person_id",
                                                      "match": "id",
                                                      "fields": {"status": ("set", 2),
                                                                 #"site_id": "remove",
                                                                 "comments": "remove",
                                                                 },
                                                      "delete": True,
                                                      "cascade": [("hrm_human_resource_tag", {"key": "human_resource_id",
                                                                                              "match": "id",
                                                                                              "fields": {"value": ("set", ANONYMOUS),
                                                                                                         },
                                                                                              "delete": True,
                                                                                              }),
                                                                  ],
                                                      }),
                              #("pr_person_user", {"key": "pe_id",
                              #                    "match": "pe_id",
                              #                    "cascade": [("auth_user", {"key": "id",
                              #                                               "match": "user_id",
                              #                                               "fields": {"id": auth.s3_anonymise_roles,
                              #                                                          "first_name": ("set", "-"),
                              #                                                          "last_name": "remove",
                              #                                                          "email": ("set", anonymous_email),
                              #                                                          "organisation_id": "remove",
                              #                                                          "password": auth.s3_anonymise_password,
                              #                                                          "deleted": ("set", True),
                              #                                                          },
                              #                                               }),
                              #                                ],
                              #                    "delete": True,
                              #                    }),
                              ],
                  "delete": True,
                  },
                 ]

        return rules

    # -------------------------------------------------------------------------
    def eac_rheader(r):
        """
            Custom rheaders
        """

        if r.representation != "html":
            # RHeaders only used in interactive views
            return None

        # Need to use this format as otherwise req_match?viewing=org_office.x
        # doesn't have an rheader
        from s3 import s3_rheader_resource, s3_rheader_tabs
        tablename, record = s3_rheader_resource(r)

        if record is None:
            # List or Create form: rheader makes no sense here
            return None

        from gluon import DIV, TABLE, TR, TH

        T = current.T

        if tablename == "cr_shelter":

            if r.method== "create":
                # The dedicated check-in pages shouldn't have an rheader to clutter things up
                return None

            tabs = [(T("Shelter Details"), None),
                    (T("Staff"), "human_resource_site"),
                    (T("Clients"), "client"),
                    #(T("Friends/Family"), "shelter_registration"),
                    (T("Event Log"), "event"),
                    ]

            rheader_tabs = s3_rheader_tabs(r, tabs)

            table = r.table
            location_id = table.location_id
            rheader = DIV(TABLE(TR(TH("%s: " % table.name.label),
                                   record.name,
                                   ),
                                TR(TH("%s: " % location_id.label),
                                   location_id.represent(record.location_id),
                                   ),
                                ),
                          rheader_tabs)

        elif tablename == "pr_person":

            tabs = [(T("Person Details"), None),
                    (T("Event Log"), "site_event"),
                    ]

            rheader_tabs = s3_rheader_tabs(r, tabs)

            if r.controller == "hrm":
                hrtable = current.s3db.hrm_human_resource
                hr = current.db(hrtable.person_id == record.id).select(hrtable.organisation_id,
                                                                       limitby = (0, 1)
                                                                       ).first()
                if hr:
                    org = TR(TH("%s: " % T("Organization")),
                             hrtable.organisation_id.represent(hr.organisation_id),
                             )
                else:
                    org = ""
            else:
                org = ""

            from s3 import s3_fullname

            rheader = DIV(TABLE(TR(TH("%s: " % T("Name")),
                                   s3_fullname(record),
                                   ),
                                org,
                                ),
                          rheader_tabs)

        return rheader

    # -------------------------------------------------------------------------
    def site_check_in(site_id, person_id):
        """
            When a person is checked-in to a Shelter then update the
            Shelter Registration

            @param site_id: the site_id of the shelter
            @param person_id: the person_id to check-in
        """

        db = current.db
        s3db = current.s3db

        # Find the Registration
        stable = s3db.cr_shelter
        rtable = s3db.cr_shelter_registration

        query = (stable.site_id == site_id) & \
                (stable.id == rtable.shelter_id) & \
                (rtable.person_id == person_id) & \
                (rtable.deleted != True)
        registration = db(query).select(rtable.id,
                                        rtable.registration_status,
                                        limitby = (0, 1)
                                        ).first()
        if not registration:
            return

        # Update the Shelter Registration
        registration.update_record(check_in_date = current.request.utcnow,
                                   registration_status = 2,
                                   )
        onaccept = s3db.get_config("cr_shelter_registration", "onaccept")
        if onaccept:
            onaccept(registration)

    # -------------------------------------------------------------------------
    def site_check_out(site_id, person_id):
        """
            When a person is checked-out from a Shelter then update the
            Shelter Registration

            @param site_id: the site_id of the shelter
            @param person_id: the person_id to check-in
        """

        db = current.db
        s3db = current.s3db

        # Find the Registration
        stable = s3db.cr_shelter
        rtable = s3db.cr_shelter_registration
        query = (stable.site_id == site_id) & \
                (stable.id == rtable.shelter_id) & \
                (rtable.person_id == person_id) & \
                (rtable.deleted != True)
        registration = db(query).select(rtable.id,
                                        rtable.registration_status,
                                        limitby = (0, 1)
                                        ).first()
        if not registration:
            return

        # Update the Shelter Registration
        registration.update_record(check_out_date = current.request.utcnow,
                                   registration_status = 3,
                                   )
        onaccept = s3db.get_config("cr_shelter_registration", "onaccept")
        if onaccept:
            onaccept(registration)

    # -------------------------------------------------------------------------
    def customise_cr_shelter_resource(r, tablename):

        from gluon import DIV, IS_IN_SET

        from s3 import S3Represent, S3SQLCustomForm, S3LocationSelector, \
                       S3TextFilter, S3LocationFilter, S3OptionsFilter, S3RangeFilter

        s3db = current.s3db

        table = s3db.cr_shelter
        table.shelter_type_id.label = T("Type")
        f = table.status
        f.default = 3 # Green
        f.requires = IS_IN_SET(cr_shelter_status_opts)
        f.represent = S3Represent(options = cr_shelter_status_opts)
        table.population_day.label = T("Occupancy")
        table.obsolete.label = T("Unavailable")
        table.obsolete.comment = DIV(_class="tooltip",
                                     _title="%s|%s" % (T("Unavailable"),
                                                       T("Site is temporarily unavailable (e.g. for building works) & so should be hidden from the map"),
                                                       ))
        table.location_id.widget = S3LocationSelector(levels = ("L3", "L4"),
                                                      required_levels = ("L3",),
                                                      show_address = True,
                                                      )

        crud_form = S3SQLCustomForm("name",
                                    "shelter_type_id",
                                    "location_id",
                                    "phone",
                                    "capacity_day",
                                    "status",
                                    "comments",
                                    "obsolete",
                                    )

        filter_widgets = [
                S3TextFilter(["name",
                              "comments",
                              "location_id$L3",
                              "location_id$L4",
                              "location_id$addr_street",
                              "location_id$addr_postcode",
                              ],
                             label = T("Search"),
                             #_class = "filter-search",
                             ),
                S3LocationFilter("location_id",
                                 label = T("Location"),
                                 levels = ("L3", "L4"),
                                 ),
                S3OptionsFilter("shelter_type_id",
                                ),
                S3OptionsFilter("status",
                                label = T("Status"),
                                options = cr_shelter_status_opts,
                                ),
                S3RangeFilter("capacity_day",
                              label = T("Total Capacity"),
                              ),
                S3RangeFilter("available_capacity_day",
                              label = T("Available Capacity"),
                              ),
                ]

        list_fields = ["name",
                       "shelter_type_id",
                       "status",
                       "capacity_day",
                       "population_day",
                       "location_id$L3",
                       "location_id$L4",
                       "location_id$addr_street",
                       ]

        report_fields = ["name",
                         "shelter_type_id",
                         "status",
                         "capacity_day",
                         "population_day",
                         "location_id$L3",
                         "location_id$L4",
                         ]

        s3db.configure(tablename,
                       create_next = None, # Don't redirect to People Registration after creation
                       crud_form = crud_form,
                       filter_widgets = filter_widgets,
                       list_fields = list_fields,
                       report_options = Storage(
                        rows = report_fields,
                        cols = report_fields,
                        fact = report_fields,
                        defaults = Storage(rows = "location_id$L4", # Lowest-level of hierarchy
                                           cols = "status",
                                           fact = "count(name)",
                                           totals = True,
                                           )
                        ),
                       site_check_in = site_check_in,
                       site_check_out = site_check_out,
                       )

    settings.customise_cr_shelter_resource = customise_cr_shelter_resource

    # -----------------------------------------------------------------------------
    def customise_cr_shelter_controller(**attr):

        from gluon import URL
        from s3 import s3_set_default_filter

        s3db = current.s3db

        # Exclude Closed Shelters by default
        s3_set_default_filter("~.status", [3, 4, 5], tablename="cr_shelter")

        # Custom Methods
        def staff_checkout(r, **attr):
            db = current.db
            shelter_id = r.id
            stable = s3db.cr_shelter
            shelter = db(stable.id == shelter_id).select(stable.site_id,
                                                         limitby = (0, 1)
                                                         ).first()
            component_id = r.component_id
            ltable = s3db.hrm_human_resource_site
            htable = s3db.hrm_human_resource
            query = (ltable.id == component_id) & \
                    (ltable.human_resource_id == htable.id)
            staff = db(query).select(htable.id,
                                     htable.person_id,
                                     limitby = (0, 1)
                                     ).first()
            # Remove Link
            db(ltable.id == component_id).delete()
            # Clear site_id
            staff.update_record(site_id = None)
            # Add Event Log entry
            s3db.org_site_event.insert(site_id = shelter.site_id,
                                       person_id = staff.person_id,
                                       event = 4, # Checked-Out
                                       )
            # Redirect
            current.session.confirmation = T("Staff checked-out succesfully!")
            from gluon import redirect
            redirect(URL(c="cr", f="shelter",
                         args = [shelter_id,
                                 "human_resource_site",
                                 ],
                         ))

        def staff_redirect(r, **attr):
            # Redirect to Staff record
            ltable = s3db.hrm_human_resource_site
            htable = s3db.hrm_human_resource
            query = (ltable.id == r.component_id) & \
                    (ltable.human_resource_id == htable.id)
            staff = current.db(query).select(htable.person_id,
                                             limitby = (0, 1)
                                             ).first()
            from gluon import redirect
            redirect(URL(c="hrm", f="person",
                         args = [staff.person_id],
                         ))

        def shelter_manage(r, **attr):
            shelter_id = r.id
            # Set this shelter into the session
            current.session.s3.shelter_id = shelter_id
            # Redirect to Normal page
            from gluon import redirect
            redirect(URL(args = [shelter_id]))

        set_method = s3db.set_method

        set_method("cr", "shelter",
                   component_name = "human_resource_site",
                   method = "checkout",
                   action = staff_checkout)

        set_method("cr", "shelter",
                   method = "manage",
                   action = shelter_manage)

        set_method("cr", "shelter",
                   component_name = "human_resource_site",
                   method = "redirect",
                   action = staff_redirect)

        s3db.add_components("cr_shelter",
                            pr_person = {"name": "client",
                                         "link": "cr_shelter_registration",
                                         "joinby": "shelter_id",
                                         "key": "person_id",
                                         "actuate": "replace",
                                         }
                            )

        s3 = current.response.s3

        # Custom prep
        standard_prep = s3.prep
        def prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            if r.component_name == "human_resource_site":

                if r.method == "create":
                    s3.crud_strings["cr_shelter"].title_display = T("Check-in Staff to %(shelter)s") % \
                                                                            {"shelter": r.record.name}

                # Filtered components
                s3db.add_components("pr_person",
                                    pr_person_tag = ({"name": "car",
                                                      "joinby": "person_id",
                                                      "filterby": {"tag": "car"},
                                                      "multiple": False,
                                                      },
                                                     ),
                                    )

                # Assigning Staff Checks them in
                def staff_check_in(form):

                    form_vars_get = form.vars.get
                    human_resource_id = form_vars_get("human_resource_id")

                    db = current.db
                    stable = s3db.cr_shelter
                    shelter = db(stable.id == r.id).select(stable.site_id,
                                                           limitby = (0, 1)
                                                           ).first()
                    site_id = shelter.site_id
                    htable = s3db.hrm_human_resource
                    staff = db(htable.id == human_resource_id).select(htable.id,
                                                                      htable.person_id,
                                                                      limitby = (0, 1)
                                                                      ).first()

                    # Set the site_id in the Staff record
                    staff.update_record(site_id = site_id)

                    # Delete old hrm_human_resource_site records
                    ltable = s3db.hrm_human_resource_site
                    query = (ltable.human_resource_id == human_resource_id) & \
                            (ltable.id != form_vars_get("id"))
                    db(query).delete()

                    # Add Site Event Log
                    s3db.org_site_event.insert(site_id = site_id,
                                               person_id = staff.person_id,
                                               event = 3, # Checked-In
                                               )

                s3db.add_custom_callback("hrm_human_resource_site",
                                         "create_onaccept",
                                         staff_check_in,
                                         )

            elif r.component_name == "human_resource":
                # UNUSED

                # Filtered components
                s3db.add_components("pr_person",
                                    pr_person_tag = ({"name": "car",
                                                      "joinby": "person_id",
                                                      "filterby": {"tag": "car"},
                                                      "multiple": False,
                                                      },
                                                     ),
                                    )

                # Override the defaulting/hiding of Organisation
                f = r.component.table.organisation_id
                f.default = None
                f.readable = f.writable = True

                # Adding Staff here Checks them in
                def staff_check_in(form):
                    table = s3db.cr_shelter
                    shelter = current.db(table.id == r.id).select(table.site_id,
                                                                  limitby = (0, 1)
                                                                  ).first()
                    s3db.org_site_event.insert(site_id = shelter.site_id,
                                               person_id = form.vars.get("person_id"),
                                               event = 3, # Checked-In
                                               )
                s3db.add_custom_callback("hrm_human_resource",
                                         "create_onaccept",
                                         staff_check_in,
                                         )
            elif r.component_name == "client":
                s3.crud_strings["cr_shelter"].title_display = T("Register Client to %(shelter)s") % \
                                                                            {"shelter": r.record.name}
            else:
                s3.crud_strings["cr_shelter"].title_update = T("Manage Shelter")

            return result
        s3.prep = prep

        # Custom postp
        standard_postp = s3.postp
        def postp(r, output):
            # Call standard postp
            if callable(standard_postp):
                output = standard_postp(r, output)

            if r.component_name == "human_resource_site":

                #from gluon import URL
                from s3 import s3_str, S3CRUD

                # Normal Action Buttons
                S3CRUD.action_buttons(r,
                                      read_url = URL(c = "cr",
                                                     f = "shelter",
                                                       args = [r.id,
                                                               "human_resource_site",
                                                               "[id]",
                                                               "redirect",
                                                               ],
                                                     ),
                                      update_url = URL(c = "cr",
                                                       f = "shelter",
                                                       args = [r.id,
                                                               "human_resource_site",
                                                               "[id]",
                                                               "redirect",
                                                               ],
                                                       ),
                                      deletable = False)

                # Custom Action Buttons
                s3.actions += [{"label": s3_str(T("Check-Out")),
                                "url": URL(c = "cr",
                                           f = "shelter",
                                           args = [r.id,
                                                   "human_resource_site",
                                                   "[id]",
                                                   "checkout",
                                                   ],
                                           ),
                                "_class": "action-btn",
                                },
                               ]

            return output
        s3.postp = postp

        attr["rheader"] = eac_rheader

        return attr

    settings.customise_cr_shelter_controller = customise_cr_shelter_controller

    # -------------------------------------------------------------------------
    def customise_cr_shelter_registration_resource(r, tablename):

        #from s3 import S3AddPersonWidget

        table = current.s3db.cr_shelter_registration
        #table.person_id.widget = S3AddPersonWidget(pe_label = True)
        f = table.registration_status
        f.default = 2 # Checked-in
        #f.readable = f.writable = False
        #table.check_out_date.readable = table.check_out_date.writable = False
        #table.comments.readable = table.comments.writable = False

    settings.customise_cr_shelter_registration_resource = customise_cr_shelter_registration_resource


    # -------------------------------------------------------------------------
    def customise_hrm_human_resource_resource(r, tablename):

        from s3 import S3AddPersonWidget, S3SQLCustomForm, \
                       S3TextFilter, S3LocationFilter, S3OptionsFilter

        s3db = current.s3db

        settings.pr.request_dob = False
        settings.pr.request_email = False
        settings.pr.request_gender = False
        settings.pr.request_tags = [(T("Car Registration"), "car"),
                                    ]

        table = s3db.hrm_human_resource
        table.person_id.widget = S3AddPersonWidget(controller = "hrm")
        table.site_id.label = T("Shelter")

        crud_form = S3SQLCustomForm("organisation_id",
                                    "site_id",
                                    "person_id",
                                    "comments",
                                    )

        filter_widgets = [
                S3TextFilter(["person_id$first_name",
                              #"person_id$middle_name",
                              "person_id$first_name",
                              "comments",
                              "organisation_id",
                              "site_id",
                              "location_id$L3",
                              "location_id$L4",
                              "person_id$car.value",
                              ],
                             label = T("Search"),
                             #_class = "filter-search",
                             ),
                S3LocationFilter("location_id",
                                 label = T("Location"),
                                 levels = ("L3", "L4"),
                                 ),
                S3OptionsFilter("organisation_id",
                                ),
                S3OptionsFilter("site_id",
                                ),
                ]

        if r.controller == "cr":
            list_fields = ["person_id",
                           "organisation_id",
                           (T("Phone"),"phone.value"),
                           (T("Car"),"person_id$car.value"),
                           ]
        else:
            list_fields = ["person_id",
                           "organisation_id",
                           "site_id",
                           "location_id$L3",
                           "location_id$L4",
                           (T("Phone"),"phone.value"),
                           (T("Car"),"person_id$car.value"),
                           ]

        report_fields = ["organisation_id",
                         "site_id",
                         "location_id$L3",
                         "location_id$L4",
                         ]

        s3db.configure(tablename,
                       crud_form = crud_form,
                       filter_widgets = filter_widgets,
                       list_fields = list_fields,
                       report_options = Storage(
                        rows = report_fields,
                        cols = report_fields,
                        fact = report_fields,
                        defaults = Storage(rows = "location_id$L4", # Lowest-level of hierarchy
                                           cols = "organisation_id",
                                           fact = "count(person_id)",
                                           totals = True,
                                           )
                        ),
                       )

    settings.customise_hrm_human_resource_resource = customise_hrm_human_resource_resource

    # -----------------------------------------------------------------------------
    def customise_hrm_human_resource_controller(**attr):

        # Filtered components
        current.s3db.add_components("pr_person",
                                    pr_person_tag = ({"name": "car",
                                                      "joinby": "person_id",
                                                      "filterby": {"tag": "car"},
                                                      "multiple": False,
                                                      },
                                                     ),
                                    )

        return attr

    settings.customise_hrm_human_resource_controller = customise_hrm_human_resource_controller


    # -------------------------------------------------------------------------
    def customise_hrm_human_resource_site_resource(r, tablename):

        from s3 import S3AddPersonWidget, S3SQLCustomForm

        s3db = current.s3db

        settings.pr.request_dob = False
        settings.pr.request_email = False
        settings.pr.request_gender = False
        settings.pr.request_tags = [(T("Car Registration"), "car"),
                                    ]

        table = s3db.hrm_human_resource_site
        table.human_resource_id.widget = S3AddPersonWidget(controller = "hrm")

        crud_form = S3SQLCustomForm("human_resource_id",
                                    )

        list_fields = ["human_resource_id$person_id",
                       "human_resource_id$organisation_id",
                       (T("Phone"),"human_resource_id$phone.value"),
                       (T("Car"),"human_resource_id$person_id$car.value"),
                       ]

        s3db.configure(tablename,
                       crud_form = crud_form,
                       list_fields = list_fields,
                       )

    settings.customise_hrm_human_resource_site_resource = customise_hrm_human_resource_site_resource

    # -------------------------------------------------------------------------
    def customise_org_organisation_resource(r, tablename):

        from s3 import S3SQLCustomForm

        s3db = current.s3db

        crud_form = S3SQLCustomForm("name",
                                    "comments",
                                    )

        list_fields = ["name",
                       ]

        s3db.configure(tablename,
                       crud_form = crud_form,
                       filter_widgets = None,
                       list_fields = list_fields,
                       )

    settings.customise_org_organisation_resource = customise_org_organisation_resource

    # -------------------------------------------------------------------------
    def customise_org_site_event_resource(r, tablename):

        from s3 import S3Represent

        current.s3db.org_site_event.status.represent = S3Represent(options = cr_shelter_status_opts)

    settings.customise_org_site_event_resource = customise_org_site_event_resource

    # -------------------------------------------------------------------------
    def customise_pr_person_resource(r, tablename):

        if r.controller == "hrm":
            # Done in prep
            return

        from gluon import IS_EMPTY_OR, IS_IN_SET

        from s3 import S3SQLCustomForm, S3SQLInlineComponent, S3LocationSelector, \
                       S3TextFilter, S3LocationFilter, S3OptionsFilter

        s3db = current.s3db
        s3 = current.response.s3

        s3.crud_strings["pr_person"] = Storage(
            label_create = T("Register a Client"),
            title_display = T("Client Details"),
            title_list = T("Clients"),
            title_update = T("Edit Client Details"),
            label_list_button = T("List Clients"),
            label_delete_button = T("Delete Client"),
            msg_record_created = T("Client added"),
            msg_record_modified = T("Client details updated"),
            msg_record_deleted = T("Client deleted"),
            msg_list_empty = T("No Clients currently registered")
            )

        f = s3db.pr_person.pe_label
        f.label = T("Reception Centre Ref")
        f.comment = None

        s3db.pr_address.location_id.widget = S3LocationSelector(levels = ("L3", "L4"),
                                                                required_levels = ("L3",),
                                                                show_address = True,
                                                                )

        # Filtered components
        s3db.add_components("pr_person",
                            pr_person_tag = ({"name": "holmes",
                                              "joinby": "person_id",
                                              "filterby": {"tag": "holmes"},
                                              "multiple": False,
                                              },
                                             {"name": "location",
                                              "joinby": "person_id",
                                              "filterby": {"tag": "location"},
                                              "multiple": False,
                                              },
                                             {"name": "pets",
                                              "joinby": "person_id",
                                              "filterby": {"tag": "pets"},
                                              "multiple": False,
                                              },
                                             {"name": "pets_details",
                                              "joinby": "person_id",
                                              "filterby": {"tag": "pets_details"},
                                              "multiple": False,
                                              },
                                             {"name": "medical",
                                              "joinby": "person_id",
                                              "filterby": {"tag": "medical"},
                                              "multiple": False,
                                              },
                                             {"name": "disability",
                                              "joinby": "person_id",
                                              "filterby": {"tag": "disability"},
                                              "multiple": False,
                                              },
                                             {"name": "dietary",
                                              "joinby": "person_id",
                                              "filterby": {"tag": "dietary"},
                                              "multiple": False,
                                              },
                                             {"name": "gp",
                                              "joinby": "person_id",
                                              "filterby": {"tag": "gp"},
                                              "multiple": False,
                                              },
                                             ),
                            )

        # Individual settings for specific tag components
        components_get = s3db.resource(tablename).components.get

        #integer_represent = IS_INT_AMOUNT.represent

        #congregations = components_get("congregations")
        #f = congregations.table.value
        #f.represent = integer_represent
        #f.requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None))

        pets = components_get("pets")
        f = pets.table.value
        f.requires = IS_EMPTY_OR(IS_IN_SET(("Y", "N")))
        f.represent = lambda v: T("yes") if v == "Y" else T("no")
        from s3 import S3TagCheckboxWidget
        f.widget = S3TagCheckboxWidget(on="Y", off="N")
        f.default = "N"

        crud_fields = ["pe_label",
                       "first_name",
                       "middle_name",
                       "last_name",
                       "gender",
                       "date_of_birth",
                       "person_details.nationality",
                       S3SQLInlineComponent(
                           "address",
                           name = "address",
                           label = T("Address"),
                           multiple = False,
                           fields = [("", "location_id")],
                           filterby = {"field": "type",
                                       "options": 1, # Current Home Address
                                       },
                       ),
                       (T("Location at Time of Incident"), "location.value"),
                       # Not a multiple=False component
                       #(T("Phone"), "phone.value"),
                       S3SQLInlineComponent(
                           "phone",
                           name = "phone",
                           label = T("Mobile Phone"),
                           multiple = False,
                           fields = [("", "value")],
                           #filterby = {"field": "contact_method",
                           #            "options": "SMS",
                           #            },
                       ),
                       S3SQLInlineComponent(
                           "email",
                           name = "email",
                           label = T("Email"),
                           multiple = False,
                           fields = [("", "value")],
                           #filterby = {"field": "contact_method",
                           #            "options": "EMAIL",
                           #            },
                       ),
                       (T("Pets"), "pets.value"),
                       (T("Details of Pets"), "pets_details.value"),
                       (T("Medical Details"), "medical.value"),
                       (T("Disability Details"), "disability.value"),
                       (T("Dietary Needs"), "dietary.value"),
                       (T("GP"), "gp.value"),
                       "comments",
                       ]

        if r.method in ("read", "update"):
            crud_fields.insert(1, (T("Holmes Ref"), "holmes.value"))

        crud_form = S3SQLCustomForm(*crud_fields)

        import json

        # Compact JSON encoding
        SEPARATORS = (",", ":")

        current.response.s3.jquery_ready.append('''S3.showHidden('%s',%s,'%s')''' % \
            ("sub_pets_value", json.dumps(["sub_pets_details_value"], separators=SEPARATORS), "pr_person"))

        filter_widgets = [
                S3TextFilter(["first_name",
                              "middle_name",
                              "last_name",
                              "pe_label",
                              "holmes.value",
                              ],
                             label = T("Search"),
                             #_class = "filter-search",
                             ),
                S3LocationFilter("location_id",
                                 label = T("Location"),
                                 levels = ("L3", "L4"),
                                 ),
                S3OptionsFilter("age_group",
                                label = T("Age"),
                                ),
                S3OptionsFilter("gender",
                                ),
                S3OptionsFilter("person_details.nationality",
                                ),
                S3OptionsFilter("pets.value",
                                label = T("Pets"),
                                ),
                ]

        list_fields = ["last_name",
                       "first_name",
                       "pe_label",
                       "gender",
                       (T("Age"), "age"),
                       ]

        report_fields = ["gender",
                         "age_group",
                         "person_details.nationality",
                         "location_id$L3",
                         "location_id$L4",
                         ]

        s3db.configure(tablename,
                       crud_form = crud_form,
                       filter_widgets = filter_widgets,
                       list_fields = list_fields,
                       report_options = Storage(
                        rows = report_fields,
                        cols = report_fields,
                        fact = report_fields,
                        defaults = Storage(rows = "location_id$L4", # Lowest-level of hierarchy
                                           cols = "age_group",
                                           fact = "count(id)",
                                           totals = True,
                                           )
                        ),
                       summary = ({"name": "table",
                                   "label": "Table",
                                   "widgets": [{"method": "datatable"}]
                                   },
                                  {"name": "report",
                                   "label": "Report",
                                   "widgets": [{"method": "report", "ajax_init": True}],
                                   },
                                  ),
                       )

    settings.customise_pr_person_resource = customise_pr_person_resource

    # -----------------------------------------------------------------------------
    def customise_pr_person_controller(**attr):

        s3 = current.response.s3

        # Custom prep
        standard_prep = s3.prep
        def prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            s3db = current.s3db

            if r.component_name == "site_event":
                f = s3db.org_site_event.site_id
                f.label = T("Shelter")
                f.readable = True
                f.represent = s3db.org_SiteRepresent(show_type = False)

            if r.controller == "hrm":
                
                from s3 import S3SQLCustomForm, S3SQLInlineComponent

                if r.method == "lookup":
                    settings.pr.request_dob = False
                    settings.pr.request_email = False
                    settings.pr.request_gender = False
                    settings.pr.request_tags = [(T("Car Registration"), "car"),
                                                ]

                # Filtered components
                s3db.add_components("pr_person",
                                    pr_person_tag = ({"name": "car",
                                                      "joinby": "person_id",
                                                      "filterby": {"tag": "car"},
                                                      "multiple": False,
                                                      },
                                                     ),
                                    )

                crud_form = S3SQLCustomForm(S3SQLInlineComponent(
                                                "human_resource",
                                                name = "human_resource",
                                                label = T("Organization"),
                                                multiple = False,
                                                fields = [("", "organisation_id")],
                                            ),
                                            "first_name",
                                            #"middle_name",
                                            "last_name",
                                            # Not a multiple=False component
                                            #(T("Phone"), "phone.value"),
                                            S3SQLInlineComponent(
                                                "phone",
                                                name = "phone",
                                                label = T("Mobile Phone"),
                                                multiple = False,
                                                fields = [("", "value")],
                                                #filterby = {"field": "contact_method",
                                                #            "options": "SMS",
                                                #            },
                                            ),
                                            (T("Car Registration"), "car.value"),
                                            "comments",
                                            )

                s3db.configure("pr_person",
                               crud_form = crud_form,
                               )

                return result

            from s3 import FS

            resource = r.resource

            # Filter out Users
            resource.add_filter(FS("user.id") == None)

            # Filter out Staff
            resource.add_filter(FS("human_resource.id") == None)

            return result
        s3.prep = prep

        attr["rheader"] = eac_rheader

        return attr

    settings.customise_pr_person_controller = customise_pr_person_controller

# END =========================================================================
