import frappe
import os
from openpyxl import load_workbook
from frappe import _


def check_and_set_branch_dimension():
    """Check if Branch accounting dimension is set, otherwise configure it"""

    # Check if Branch dimension exists
    branch_dimension = frappe.db.exists("Accounting Dimension", "Branch")

    if not branch_dimension:
        print("Branch accounting dimension not found. Creating it...")
        create_branch_dimension()
    else:
        print("Branch accounting dimension already exists.")
        # Verify it's properly configured
        verify_branch_dimension()


def create_branch_dimension():
    """Create Branch accounting dimension"""
    try:
        dimension = frappe.get_doc(
            {
                "doctype": "Accounting Dimension",
                "document_type": "Branch",
                "dimension_name": "Branch",
                "disabled": 0,
                "company": "",  # Applies to all companies
            }
        )
        dimension.insert(ignore_permissions=True)
        frappe.db.commit()
        print("✓ Branch accounting dimension created successfully")

        # Enable dimension in Company settings
        enable_dimension_in_companies()

    except Exception as e:
        print(f"✗ Failed to create Branch dimension: {str(e)}")
        frappe.log_error(f"Failed to create Branch dimension: {str(e)}")


def verify_branch_dimension():
    """Verify Branch dimension is properly configured"""
    dimension = frappe.get_doc("Accounting Dimension", "Branch")

    if dimension.disabled:
        print("Branch dimension is disabled. Enabling it...")
        dimension.disabled = 0
        dimension.save(ignore_permissions=True)
        frappe.db.commit()
        print("✓ Branch dimension enabled")

    # Check if dimension is enabled in companies
    enable_dimension_in_companies()


def enable_dimension_in_companies():
    """Enable Branch dimension in all companies"""
    companies = frappe.get_all("Company", pluck="name")

    for company in companies:
        company_doc = frappe.get_doc("Company", company)

        # Check if Branch is in accounting dimensions
        dimension_exists = False
        for dim in company_doc.accounting_dimensions:
            if dim.dimension == "Branch":
                dimension_exists = True
                if dim.disabled:
                    dim.disabled = 0
                    print(f"✓ Enabled Branch dimension in {company}")
                break

        # Add Branch dimension if not exists
        if not dimension_exists:
            company_doc.append(
                "accounting_dimensions", {"dimension": "Branch", "disabled": 0}
            )
            print(f"✓ Added Branch dimension to {company}")

        company_doc.save(ignore_permissions=True)

    frappe.db.commit()
    print("✓ Branch dimension enabled in all companies")


def set_default_dimension_values():
    """Set default dimension values for existing accounts"""
    try:
        # Get all accounts
        accounts = frappe.get_all(
            "Account", filters={"company": ["!=", ""]}, fields=["name", "company"]
        )

        for account in accounts:
            account_doc = frappe.get_doc("Account", account.name)

            # Check if branch dimension field exists and is empty
            if hasattr(account_doc, "branch") and not account_doc.branch:
                # Set default branch based on company
                default_branch = frappe.db.get_value(
                    "Branch", {"company": account.company, "is_default": 1}, "name"
                )

                if default_branch:
                    account_doc.branch = default_branch
                    account_doc.save(ignore_permissions=True)
                    print(f"✓ Set default branch for account: {account.name}")

        frappe.db.commit()

    except Exception as e:
        print(f"Note: Could not set default dimension values: {str(e)}")


def after_install():
    print("Starting account import...")
    # Ensure Branch dimension is set up
    check_and_set_branch_dimension()
    # Get the default company
    default_company = frappe.db.get_single_value("Global Defaults", "default_company")
    if not default_company:
        default_company = frappe.db.get_value("Company", {}, "name")

    if not default_company:
        frappe.throw("No Company found. Please create a Company first.")

    print(f"Using company: {default_company}")

    # Import accounts
    import_accounts_from_excel(default_company, "roots_accounts.xlsx")
    import_accounts_from_excel(default_company, "accounts.xlsx")
    print("Account import completed successfully!")


def import_accounts_from_excel(company, filename):
    """Import accounts from Excel file without relying on autoname"""

    file_path = frappe.get_app_path("transfer", "public", "asset", "xlsx", filename)

    if not os.path.exists(file_path):
        print(f"File not found, skipping: {filename}")
        return

    print(f"Importing accounts from: {filename}")

    workbook = load_workbook(file_path)
    sheet = workbook.active
    abbr = frappe.db.get_value("Company", company, "abbr") or "CO"

    accounts = []

    # Read accounts from Excel
    for row_idx, row in enumerate(
        sheet.iter_rows(min_row=2, values_only=True), start=2
    ):
        # Skip empty rows
        if not any(row) or not row[1]:  # row[1] is account_name
            continue

        try:
            account_data = {
                "doctype": "Account",
                "account_name": str(row[1]).strip(),
                "account_number": str(row[2]).strip() if row[2] else "",
                "is_group": bool(int(row[3])) if row[3] is not None else False,
                "account_currency": str(row[4]).strip() if row[4] else "LYD",
                "company": company,
                "report_type": "Balance Sheet",
                "root_type": str(row[5]).strip() if row[5] else "",
                "account_type": str(row[6]).strip() if row[6] else "Asset",
            }

            # Set parent account for non-group accounts
            if not account_data["is_group"] and row[5]:
                account_data["parent_account"] = str(row[5]).strip()

            # MANUALLY set the account name to avoid autoname issues
            if account_data["account_number"]:
                account_data["name"] = (
                    f"{account_data['account_number']} - {account_data['account_name']} - {abbr}"
                )
            else:
                account_data["name"] = f"{account_data['account_name']} - {abbr}"

            accounts.append(account_data)

        except Exception as e:
            print(f"Error processing row {row_idx}: {e}")
            continue

    # Import accounts in order (groups first)
    group_accounts = [acc for acc in accounts if acc["is_group"]]
    child_accounts = [acc for acc in accounts if not acc["is_group"]]

    # Import group accounts first
    for account in group_accounts:
        create_account(account)

    # Import child accounts
    for account in child_accounts:
        create_account(account)


def create_account(account_data):
    """Create a single account with proper error handling"""

    try:
        # Check if account already exists
        if frappe.db.exists("Account", account_data["name"]):
            print(f"✓ Account already exists: {account_data['name']}")
            return

        # Create the account
        doc = frappe.get_doc(account_data)
        doc.insert(
            ignore_permissions=True,
            ignore_links=True,
            ignore_mandatory=True,
            ignore_if_duplicate=True,
        )

        print(f"✓ Created account: {account_data['name']}")
        frappe.db.commit()

    except frappe.DuplicateEntryError:
        print(f"✓ Account already exists (duplicate): {account_data['name']}")
    except Exception as e:
        print(f"✗ Failed to create account {account_data['name']}: {str(e)}")
        frappe.log_error(f"Account creation failed: {str(e)}")


def after_uninstall():
    """Clean up accounts on uninstall"""
    print("Uninstalling transfer app accounts...")

    # Get accounts to delete from both files
    accounts_to_delete = []

    for filename in ["roots_accounts.xlsx", "accounts.xlsx"]:
        file_path = frappe.get_app_path("transfer", "public", "asset", "xlsx", filename)

        if os.path.exists(file_path):
            try:
                workbook = load_workbook(file_path)
                sheet = workbook.active

                for row in sheet.iter_rows(min_row=2, values_only=True):
                    if row[1]:  # account_name
                        accounts_to_delete.append(str(row[1]).strip())

            except Exception as e:
                print(f"Error reading {filename}: {e}")

    # Delete accounts
    for account_name in accounts_to_delete:
        try:
            if frappe.db.exists("Account", {"account_name": account_name}):
                frappe.delete_doc("Account", account_name, ignore_permissions=True)
                print(f"Deleted account: {account_name}")
        except Exception as e:
            print(f"Failed to delete account {account_name}: {e}")

    print("removing accounts completed")
