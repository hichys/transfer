import frappe
import csv
import os
from openpyxl import load_workbook


def after_install():
    import_accounts_from_excel()


def import_accounts_from_excel():
    file_path = frappe.get_app_path(
        "transfer", "public", "asset", "xlsx", "accounts.xlsx"
    )

    if not os.path.exists(file_path):
        frappe.throw(f"File not found: {file_path}")

    workbook = load_workbook(file_path)
    sheet = workbook.active  # Use the first sheet in the workbook

    for row in sheet.iter_rows(min_row=2, values_only=True):  # Skip the header row
        account_data = {
            "doctype": "Account",
            "name": row[0],  # ID
            "account_name": row[1],  # Account Name
            "account_number": row[2] or "",  # Account Number
            "is_group": int(row[3]),  # Is Group
            "account_currency": row[4],  # Currency
            "parent_account": row[5] or "",  # Parent Account
            "account_type": row[6] or "",  # Account Type
            "company": "alalmia",  # Adjust company name as needed
            "report_type": "Balance Sheet",
            "root_type": "Asset" if row[6] == "Asset" else "",
        }

        # Check if account already exists
        if not frappe.db.exists(
            "Account",
            {"account_name": account_data["account_name"], "company": "alalmia"},
        ):
            frappe.get_doc(account_data).insert(ignore_permissions=True)
            print(f"Inserted account: {account_data['account_name']}")
        else:
            print(f"Account already exists: {account_data['account_name']}")
