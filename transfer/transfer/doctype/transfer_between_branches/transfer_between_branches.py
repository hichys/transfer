# Copyright (c) 2024, a and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from transfer.transfer.api import get_account_for_branch
from .create_journal_entery import *

class transferbetweenbranches(Document):
    # Events triggered when the document is saved or modified
    def on_trash(self):
        frappe.msgprint("This document has been trashed")

    def before_cancel(self):
        create_journal_entry_from_canceled_transfer(self, method="submit")
        #self.docstast = "إلغاء"
        frappe.msgprint("This document has been canceled successfully")

    def after_insert(self):
        if self.workflow_state == "معلقة" and not self.notyet:
            debit = get_account_for_branch(branch_name=self.from_branch, account_index=0)
            credit = get_account_for_branch(branch_name=self.to_branch, account_index=1)
            self.debit = debit
            self.credit = credit
            create_journal_entry_from_pending_transfer(self, method="submit")

    def on_change(self):
        frappe.msgprint("on change: " + self.workflow_state)
        if self.workflow_state == "تم التسليم" and not self.handed:
            debit = get_account_for_branch(branch_name=self.to_branch, account_index=1)
            credit = get_account_for_branch(branch_name=self.to_branch, account_index=0)
            self.debit = debit
            self.credit = credit
            create_journal_entry_from_handed_transfer(self, method="submit")
        elif self.workflow_state == "إلغاء" and not self.canceld_journal_entry:
            debit = get_account_for_branch(branch_name=self.to_branch, account_index=1)
            credit = get_account_for_branch(branch_name=self.from_branch, account_index=0)
            self.debit = debit
            self.credit = credit
            create_journal_entry_from_canceled_transfer(self, method="submit")

    def on_update(self):
        print("on update called")
        self.transfer()

    def on_submit(self):
        print("on submit called")

    def on_save(self):
        frappe.msgprint("تم تسجيل الحوالة في المنظومة بنجاح")

    def transfer(self):
        amount = self.amount
        commission_amount = self.profit
        debit = self.debit
        credit = self.credit

@frappe.whitelist()
def test(docname):
    frappe.msgprint("This document has been trashed")

@frappe.whitelist()
def delete_current_doc(docname,method="submit"):
    frappe.msgprint("Deleting Document")
    try:
        # Use frappe.delete_doc to delete the document
        frappe.delete_doc("transfer between branches", docname)
        frappe.db.commit()
        frappe.msgprint(f"Document {docname} deleted successfully.")
        return {"status": "success", "message": f"Document {docname} deleted successfully."}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error Deleting Document")
        frappe.msgprint(f"Error occurred while deleting the document: {str(e)}")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def on_status_change(doc, method):
    pass

def create_journal_entry_from_pending_transfer(doc, method):
    commision = doc.profit / 2
    debit_with_commision = doc.amount + doc.profit
    to_profit_account = get_account_for_branch(doc.from_branch, 2)
    from_profit_account = get_account_for_branch(doc.to_branch, 2)

    accounts = [
        {
            "account": doc.debit,
            "branch": doc.from_branch,
            "debit_in_account_currency": debit_with_commision,
            "credit_in_account_currency": 0,
        },
        {
            "account": doc.credit,
            "branch": doc.to_branch,
            "debit_in_account_currency": 0,
            "credit_in_account_currency": doc.amount,
        }
    ]

    if commision != 0:
        accounts.extend([
            {
                "account": to_profit_account,
                "branch": doc.from_branch,
                "debit_in_account_currency": 0,
                "credit_in_account_currency": commision,
            },
            {
                "account": from_profit_account,
                "branch": doc.to_branch,
                "debit_in_account_currency": 0,
                "credit_in_account_currency": commision,
            }
        ])

    journal_entry = frappe.get_doc({
        "doctype": "Journal Entry",
        "posting_date": doc.posting_date,
        "mode_of_payment": "Cash",
        "accounts": accounts
    })

    
    
    journal_entry.insert(ignore_permissions=True)
    journal_entry.custom_state = doc.docstatus
    doc.journal_entry = journal_entry.name
    doc.notyet = journal_entry.name
    doc.journal_entry_link = f'<button class="btn btn-primary" onclick="window.open(\'/app/journal-entry/{journal_entry.name}\', \'_blank\')">View Journal Entry</button>'
    doc.save()
    frappe.db.commit()
    journal_entry.submit()
    frappe.publish_realtime("refresh_ui", {"docname": doc.name, "journal_entry": journal_entry.name}, user=frappe.session.user)
    frappe.msgprint(doc.journal_entry_link)
    frappe.msgprint(f"Journal Entry {journal_entry.name} created and linked to the Transfer Between Branches document.")

@frappe.whitelist()
def cancel_notyet_transaction(docname, method):
    frappe.msgprint("جاري إلغاء الحوالة الغير مستلمة")
    try:
        # Fetch the document
        doc = frappe.get_doc('transfer between branches', docname)

        # Check if already canceled by workflow state
        if doc.workflow_state == "إلغاء":
            frappe.msgprint("هذه الحوالة ملغية مسبقا")
            return {"status": "error", "message": "This document is already cancelled."}

        # Check if the document status is already canceled
        if doc.docstatus == 2:
            frappe.msgprint("This document is already cancelled.")
            return {"status": "error", "message": "This document is already cancelled."}

        # Fetch the "notyet" Journal Entry linked to the document
        if doc.notyet:
            notyet = frappe.get_doc('Journal Entry', doc.notyet)

            # Cancel the Journal Entry if not already canceled
            if notyet.docstatus == 2:
                frappe.msgprint(f"Not Yet Entry {notyet.name} is already canceled.")
            else:
                notyet.cancel()
                frappe.msgprint("Journal Entry canceled successfully.")
        
        # Update the workflow state
        doc.workflow_state = "تم الإلغاء"
        doc.save()
        frappe.db.commit()

        frappe.msgprint("Document has been successfully updated to 'إلغاء'.")
        return {"status": "success", "message": "Document and linked Journal Entry have been cancelled."}

    except frappe.DoesNotExistError:
        frappe.throw("Journal Entry does not exist.")
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error Cancelling Transaction")
        frappe.throw(str(e))

@frappe.whitelist()
def cancel_trnasfer_after_aday(docname,method):
    frappe.msgprint("cancel_trnasfer_after_aday")

@frappe.whitelist()
def create_journal_entry_from_canceled_transfer(docname, method):
    frappe.msgprint("create_journal_entry_from_canceled_transfer is called")
    try:
        doc = frappe.get_doc('transfer between branches', docname)

        if(doc.workflow_state == "إلغاء"):
            doc.workflow_state  = "إلغاء"
            doc.save()
            frappe.msgprint("This document is already cancelled.")
            return {"status": "error", "message": "This document is already cancelled."}
        
        try:
            handed = frappe.get_doc('Journal Entry', doc.handed)
            
            handed.cancel()
                    
                
            notyet = frappe.get_doc('Journal Entry', doc.notyet)        
           
            notyet.cancel()
                
                
            doc.workflow_state = "تم الإلغاء"
            doc.save()
            frappe.db.commit()
            
            
            frappe.msgprint("Journal Entries canceled successfully.")
        except frappe.DoesNotExistError:
            frappe.throw("Journal Entrieseeee do not exist.")
        except Exception as je_error:
            frappe.log_error(frappe.get_traceback(), "Error Cancelling Journal Entry")
            frappe.throw(str(je_error))


        frappe.log_error(f"Document {docname} cancelled.", "Document Cancellation")
        frappe.msgprint(f"Document {docname} and its linked Journal Entry (if any) have been successfully cancelled.")

        return {"status": "success", "message": "Document and linked Journal Entry have been cancelled."}

    except Exception as e:
        frappe.throw(str(e))
        frappe.log_error(frappe.get_traceback(), "Error in on_trash_handler")
        return {"status": "error", "message": str(e)}
    

@frappe.whitelist()
def create_journal_entry_from_handed_transfer(doc, method):
    debit_to_liabilities = get_account_for_branch(doc.to_branch, 1)
    credit_to_account = get_account_for_branch(doc.to_branch, 0)
    journal_entry = frappe.get_doc({
        "doctype": "Journal Entry",
        "posting_date": doc.posting_date,
        "accounts": [
            {
                "account": debit_to_liabilities,
                "debit_in_account_currency": doc.amount,
                "credit_in_account_currency": 0,
            },
            {
                "account": credit_to_account,
                "debit_in_account_currency": 0,
                "credit_in_account_currency": doc.amount,
            }
        ]
    })

    journal_entry.custom_state = doc.docstatus
    journal_entry.insert(ignore_permissions=True)
    journal_entry.posting_date = doc.delivery_date
    doc.journal_entry = journal_entry.name
    doc.handed = journal_entry.name
    
    doc.save()
    frappe.db.commit()
    journal_entry.submit()

    frappe.publish_realtime("refresh_ui", {"docname": doc.name, "journal_entry": journal_entry.name}, user=frappe.session.user)

@frappe.whitelist()
def create_journal_entry_from_handed_transfer(doc, method):
    debit_to_liabilities = get_account_for_branch(doc.to_branch, 1)
    credit_to_account = get_account_for_branch(doc.to_branch, 0)
    journal_entry = frappe.get_doc({
        "doctype": "Journal Entry",
        "posting_date": doc.posting_date,
        "accounts": [
            {
                "account": debit_to_liabilities,
                "debit_in_account_currency": doc.amount,
                "credit_in_account_currency": 0,
            },
            {
                "account": credit_to_account,
                "debit_in_account_currency": 0,
                "credit_in_account_currency": doc.amount,
            }
        ]
    })

    journal_entry.custom_state = doc.docstatus
    journal_entry.insert(ignore_permissions=True)
    journal_entry.posting_date = doc.delivery_date
    doc.journal_entry = journal_entry.name
    doc.handed = journal_entry.name
    
    doc.save()
    frappe.db.commit()
    journal_entry.submit()

    frappe.publish_realtime("refresh_ui", {"docname": doc.name, "journal_entry": journal_entry.name}, user=frappe.session.user)

@frappe.whitelist()
def reverse_journal_entry(doc):
		original_entry = frappe.get_doc("Journal Entry", doc.journal_entry)
		accounts = []

		for line in original_entry.accounts:
			accounts.append({
				"account": line.account,
				"debit_in_account_currency": line.credit_in_account_currency,
				"credit_in_account_currency": line.debit_in_account_currency
			})
		
		reversal_entry = frappe.get_doc({
			"doctype": "Journal Entry",
			"posting_date": frappe.utils.nowdate(),
			"accounts": accounts
		})
		reversal_entry.insert(ignore_permissions=True)
		reversal_entry.submit()
		doc.reversal_journal_entry = reversal_entry.name
		doc.save()
