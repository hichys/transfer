# Copyright (c) 2025, awad mohamed & atta almanan and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class TransferSetting(Document):
	def validate(self):
		validate_transfer_setting(self, "validate")



def get_customer_accounts(customer_name, is_internal=True):
    """Return the expected account names (whether they exist or not)."""
    company = frappe.defaults.get_global_default("company")
    cash_acc_name = f"{customer_name} - Cash"
    profit_acc_name = f"{customer_name} - Profit" if is_internal else None

    cash_account = frappe.db.get_value(
        "Account", {"account_name": cash_acc_name, "company": company}
    )
    profit_account = None
    if is_internal:
        profit_account = frappe.db.get_value(
            "Account", {"account_name": profit_acc_name, "company": company}
        )

    return cash_account, profit_account


def get_or_create_customer_accounts(customer_name, is_internal=True):
    company = frappe.defaults.get_global_default("company")

    # Ensure Customer exists
    customer = frappe.db.get_value("Customer", {"customer_name": customer_name}, "name")
    if not customer:
        customer_doc = frappe.get_doc(
            {
                "doctype": "Customer",
                "customer_name": customer_name,
                "customer_type": "Individual",
                "customer_group": frappe.db.get_single_value(
                    "Selling Settings", "customer_group"
                )
                or "All Customer Groups",
                "territory": frappe.db.get_single_value("Selling Settings", "territory")
                or "All Territories",
            }
        )
        customer_doc.insert(ignore_permissions=True)
        customer = customer_doc.name

    # Ensure Accounts exist
    profit_parent = frappe.get_value(
        "Account", {"account_name": "Customer Profits", "company": company}, "name"
    )
    cash_parent = frappe.get_value(
        "Account", {"account_name": "Customer Cash", "company": company}, "name"
    )

    if not cash_parent:
        frappe.throw(
            "Please create 'Customer Cash' parent account in Chart of Accounts."
        )

    cash_acc_name = f"{customer_name} - Cash"
    profit_acc_name = f"{customer_name} - Profit"

    cash_account = frappe.db.get_value(
        "Account", {"account_name": cash_acc_name, "company": company}
    )
    if not cash_account:
        cash_doc = frappe.get_doc(
            {
                "doctype": "Account",
                "account_name": cash_acc_name,
                "parent_account": cash_parent,
                "company": company,
                "account_type": "Cash",
                "is_group": 0,
            }
        )
        cash_doc.insert(ignore_permissions=True)
        cash_account = cash_doc.name

    profit_account = None
    if is_internal:
        if not profit_parent:
            frappe.throw(
                "Please create 'Customer Profits(Income)' parent account in Chart of Accounts."
            )

        profit_account = frappe.db.get_value(
            "Account", {"account_name": profit_acc_name, "company": company}
        )
        if not profit_account:
            profit_doc = frappe.get_doc(
                {
                    "doctype": "Account",
                    "account_name": profit_acc_name,
                    "parent_account": profit_parent,
                    "company": company,
                    "account_type": "Income Account",
                    "is_group": 0,
                }
            )
            profit_doc.insert(ignore_permissions=True)
            profit_account = profit_doc.name

    return customer, cash_account, profit_account


def validate_transfer_setting(doc, method):
    """
    Hook this to Transfer Setting -> validate
    Ensures customers + accounts are created
    Updates child table with account links
    """
    # Internal customers
    for row in doc.internal:
        customer, cash_acc, profit_acc = get_or_create_customer_accounts(
            row.customer, is_internal=True
        )
        row.cash_account = cash_acc
        row.profit_account = profit_acc

    # External customers
    for row in doc.external:
        customer, cash_acc, _ = get_or_create_customer_accounts(
            row.customer, is_internal=False
        )
        row.cash_account = cash_acc
        row.profit_account = None
