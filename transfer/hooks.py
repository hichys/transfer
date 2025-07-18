app_name = "transfer"
app_title = "transfer"
app_publisher = "awad mohamed & atta almanan"
app_description = "transfer"
app_email = "awd@hotmail.it"
app_license = "mit"


app_logo_url = "/assets/transfer/images/logo.png"
# Apps
# ------------------
boot_session = "transfer.startup.boot_session"

# required_apps = []
required_apps = ["erpnext"]
# Each item in the list will be shown as an app in the apps page
add_to_apps_screen = [
    {
        "name": "transfer",
        "logo": "/assets/transfer/images/logo.png",
        "title": "transfer",
        "route": "/app/alalmiatransfer",
    }
]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html

app_include_js = [
    "/assets/transfer/js/utils.js",
    "/assets/transfer/js/redirect.js",
    "/assets/transfer/js/custom.js",
]

app_include_css = "/assets/transfer/css/custom.css"

# include js, css files in header of web template
# web_include_css = "/assets/transfer/css/transfer.css"
# web_include_js = "/assets/transfer/js/transfer.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "transfer/public/scss/website"
fixtures = [
    "Workflow",
    "Custom Field",
    "Property Setter",
    "Print Format",
    "Account",
    "Branch",
    "Customer",
    "Item",
    "BranchAccounts",
    "Role",
]
# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "transfer/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"
home_page = "/app/alalmiatransfer"
# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "transfer.utils.jinja_methods",
# 	"filters": "transfer.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "transfer.install.before_install"
after_install = "transfer.install.after_install"

# Uninstallation
# ------------

before_uninstall = "transfer.install.after_uninstall"
# after_uninstall = "transfer.install.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "transfer.utils.before_app_install"
# after_app_install = "transfer.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "transfer.utils.before_app_uninstall"
# after_app_uninstall = "transfer.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "transfer.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    "transfer between branches": {
        # "on_update": "transfer.transfer.doctype.transfer_between_branches.on_status_change",
        # "on_cancel": "method",
        # "on_trash": "transfer.transfer.doctype.transfer_between_branches.transfer_between_branches.delete_current_doc",
    }
}
# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"transfer.tasks.all"
# 	],
# 	"daily": [
# 		"transfer.tasks.daily"
# 	],
# 	"hourly": [
# 		"transfer.tasks.hourly"
# 	],
# 	"weekly": [
# 		"transfer.tasks.weekly"
# 	],
# 	"monthly": [
# 		"transfer.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "transfer.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "transfer.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "transfer.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["transfer.utils.before_request"]
# after_request = ["transfer.utils.after_request"]

# Job Events
# ----------
# before_job = ["transfer.utils.before_job"]
# after_job = ["transfer.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]
# loading screen
website_context = {
    "splash_image": "/assets/transfer/images/logo.png",
    "favicon": "/assets/transfer/images/favicon.ico"
}

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"transfer.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }
