import frappe
import os
from openpyxl import load_workbook

default_company = None

def after_install():
    print("Creating Account script is running...")
    import_accounts_from_excel("roots_accounts.xlsx")

    # Fetch default company if set
    default_company = frappe.db.get_single_value("Global Defaults", "default_company")

    if not default_company:
        # If no default company, just pick the first one
        default_company = frappe.db.get_value("Company", {}, "name")

    else:
        default_company = input("Enter the company name for accounts (imported from public folder): ")

    if(default_company):
        print(f"Default company set to: {default_company} importing accounts...")
        import_accounts_from_excel(default_company)

    if not default_company:
        frappe.throw(
            "No Company found. Please create a Company before installing this app."
        )
        frappe.log_error("after_install script is running...", "Custom App Installation")

    # Example: create some Accounts under this company


def import_accounts_from_excel(default_company=None, filename="accounts.xlsx"):
    file_path = frappe.get_app_path("transfer", "public", "asset", "xlsx", filename)

    if not os.path.exists(file_path):
        frappe.throw(f"File not found: {file_path}")

    # Load the workbook and sheet
    workbook = load_workbook(file_path)
    sheet = workbook.active  # Use the first sheet in the workbook

    accounts = []

    # Step 1: Read and store all account data
    for row in sheet.iter_rows(min_row=2, values_only=True):  # Skip the header row
        isgroup = row[3] == 1
        if not isgroup:
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
        else:
            account_data = {
                "doctype": "Account",
                "name": row[0],  # ID
                "account_name": row[1],  # Account Name
                "account_number": row[2] or "",  # Account Number
                "is_group": int(row[3]),  # Is Group
                "account_currency": row[4],  # Currency
                "root_type": row[5] or "",  # Parent Account
                "account_type": row[6] or "",  # Account Type
                "company": "alalmia",  # Adjust company name as needed
                "report_type": "Balance Sheet",
            }
        accounts.append(account_data)

    # Step 2: First insert all group accounts (is_group = 1) and then insert child accounts (is_group = 0)
    for account in sorted(accounts, key=lambda x: x["is_group"], reverse=True):
        # Check if account already exists
        if not frappe.db.exists(
            "Account",
            {"account_name": account["account_name"], "company": default_company},
        ):
            # Insert parent accounts first (where is_group = 1)
            frappe.get_doc(account).insert(
                ignore_permissions=True,
                ignore_if_duplicate=True,
                ignore_mandatory=True,
                ignore_links=True,
            )
            print(f"Inserted account: {account['account_name']}")
            frappe.db.commit()
        else:
            print(f"Account already exists: {account['account_name']}")

    frappe.db.commit()  # Committing changes after all records are inserted


def get_account_from_xlsx(filename="accounts.xlsx"):
    file_path = frappe.get_app_path("transfer", "public", "asset", "xlsx", filename)

    if not os.path.exists(file_path):
        frappe.throw(f"File not found: {file_path}")

    # Load the workbook and sheet
    workbook = load_workbook(file_path)
    sheet = workbook.active  # Use the first sheet in the workbook

    accounts = []

    # Step 1: Read and store all account data
    for row in sheet.iter_rows(min_row=2, values_only=True):  # Skip the header row
        account_data = {
            "name": row[0],  # ID
        }
        accounts.append(account_data)

    return accounts


def after_uninstall():
    print("after_uninstall script is running...")
    frappe.log_error(
        "after_uninstall script is running...", "Custom App Uninstallation"
    )

    accounts = []
    accounts.extend(get_account_from_xlsx("roots_accounts.xlsx"))
    accounts.extend(get_account_from_xlsx("accounts.xlsx"))

    # Identify and delete the accounts added by your custom app

    for account in accounts:
        try:
            # Delete the account if it exists
            frappe.delete_doc("Account", account, ignore_permissions=True)
            print(f"Deleted account: {account}")
            frappe.db.commit()
        except Exception as e:
            print(f"Failed to delete account: {account} - {str(e)}")
            frappe.log_error(
                f"Failed to delete account: {account} - {str(e)}",
                "Account Deletion Error",
            )

    # C
