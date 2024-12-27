import frappe
from frappe.model.document import Document
from transfer.transfer.api import get_account_for_branch

@frappe.whitelist()
def transfer_created(debit, credit,
                     debit_profit_account,credit_profit_account,
                     debit_profit,credit_profit,
                     debit_branch, credit_branch,
                     remarks,posting_date):
    frappe.msgprint(f"transfer_created() ")
    

@frappe.whitelist()
def transfer_delievred():
    frappe.msgprint(f"transfer_delievred() ")

@frappe.whitelist()
def transfer_canceled():
    frappe.msgprint(f"transfer_canceled() ")
    
    