import frappe

def boot_session(bootinfo):
    if frappe.session.user != "Guest":
        frappe.local.response["home_page"] = "/app/alalmiatransfer"
