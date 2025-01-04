# Copyright (c) 2024, a and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from transfer.transfer.api import get_account_for_branch,get_main_account,get_temp_account,get_profit_account
from .create_journal_entery import *

class transferbetweenbranches(Document):
    # Events triggered when the document is saved or modified
    def on_trash(self):
        frappe.msgprint("This document has been trashed")

    def before_cancel(self):
        #get all journal enteries linked cheque_no to this document make sure its canceled or reversed
        
        #get jouranl enteries from db thats has the same docname == cheque_no

        doc = frappe.get_doc('transfer between branches', self.name)
        journal_entries = frappe.get_all("Journal Entry", filters={"cheque_no": doc.name}, fields=["name", "docstatus"])
        if journal_entries:
            for entry in journal_entries:
                #check if reversal_of is not empty meaing this journal entry is reversed
                if entry.docstatus == 1 and entry.reversal_of and entry.custom_reversed_by:
                    frappe.throw(f"Journal Entry {entry.name} is not canceled or reversed.")
                
        else:
            frappe.throw("Error code 404")

  
        # frappe.msgprint("This document has been canceled successfully")
        self.workflow_state = "ملغية"

    def after_insert(self):
        pass
      # Save the previous state when the document is loaded

    def on_change(self):
        # check previous state
        if(self.get_doc_before_save() and not self.get_doc_before_save().workflow_state == "مستلمة"):
            

            if self.workflow_state == "مستلمة" and not self.handed:
                frappe.msgprint("تم التسليم **3434***")
                debit = get_account_for_branch(branch_name=self.to_branch, account_index=1)
                credit = get_account_for_branch(branch_name=self.to_branch, account_index=0)
                self.debit = debit
                self.credit = credit
                create_journal_entry_from_handed_transfer(self, method="submit")
        # elif self.workflow_state == "إلغاء الحوالة" and not self.canceld_journal_entry:
        #     debit = get_account_for_branch(branch_name=self.to_branch, account_index=1)
        #     credit = get_account_for_branch(branch_name=self.from_branch, account_index=0)
        #     self.debit = debit
        #     self.credit = credit
        #     create_journal_entry_from_canceled_transfer(self, method="submit")

    def on_update(self):
        print("on update called")
        self.transfer()

    def on_submit(self):
        if self.workflow_state == "غير مستلمة" and not self.notyet:
            debit = get_main_account(self.from_branch)
            credit = get_temp_account(self.to_branch)
            self.debit = debit
            self.credit = credit
            create_journal_entry_from_pending_transfer(self, method="submit")

    def on_save(self):
        frappe.msgprint("تم تسجيل الحوالة في المنظومة بنجاح")

    def transfer(self):
        amount = self.amount
        commission_amount = self.total_profit
        debit = self.debit
        credit = self.credit

@frappe.whitelist()
def test(docname):
    frappe.msgprint("This document has been trashed")
@frappe.whitelist()
def handel_cancelation(docname, method):
    # if method == "reversal": revese it
    # else if method == cancel then cancel it

    if method == "reversal":
        cancel_notyet_transaction(docname, method="reversal")
    elif method == "cancel":
        create_journal_entry_from_canceled_transfer(docname, method="cancel")
    else:
        frappe.throw("Invalid method. Please provide a valid method.")


 
def create_journal_entry_from_pending_transfer(doc, method):
    # show alert
    frappe.msgprint("create_journal_entry_from_pending_transfer is called")
    



    debit_with_commision = doc.amount + doc.total_profit

    from_main_account = get_main_account(doc.from_branch)
    to_main_account = get_main_account(doc.to_branch)

    to_temp_account = get_temp_account(doc.to_branch)

    from_profit_account = get_profit_account(doc.from_branch)
    to_profit_account = get_profit_account(doc.to_branch)
    
    
    accounts = [
        {
            "account": from_main_account,
            "branch": doc.from_branch,
            "debit_in_account_currency": debit_with_commision,
            "credit_in_account_currency": 0,
        },
        {
            "account": to_temp_account,
            "branch": doc.to_branch,
            "debit_in_account_currency": 0,
            "credit_in_account_currency": doc.amount,
        }
    ]

  
    from_profit = doc.our_profit
    to_profit = doc.other_party_profit
    if from_profit > 0 :
        accounts.extend([
            {
                "account": from_profit_account,
                "branch": doc.from_branch,
                "debit_in_account_currency": 0,
                "credit_in_account_currency": from_profit,
            }
        ])
    if to_profit  > 0:
        accounts.extend([
            {
                "account": to_profit_account,
                "branch": doc.to_branch,
                "debit_in_account_currency": 0,
                "credit_in_account_currency": to_profit,
            }
        ])

    journal_entry = frappe.get_doc({
        "doctype": "Journal Entry",
        "posting_date": doc.posting_date,
        "mode_of_payment": "Cash",
        "accounts": accounts,
        "cheque_no" : doc.name,
        "cheque_date" : doc.posting_date
    })

    
    
    try:
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
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error Creating Journal Entry")
        frappe.throw(f"An error occurred while creating the Journal Entry: {e}")    



@frappe.whitelist()
def cancel_notyet_transaction(docname, method ):
    frappe.msgprint("cancel_notyet_transaction is called")
    try:
        # Fetch the document
        try :
            doc = frappe.get_doc('transfer between branches', docname)
        except frappe.DoesNotExistError:
            frappe.throw("الرجاء انشاء الحوالة اولا")
            return
        
        # Check if the 'handed' journal entry exists
        if doc.handed:
            if method == "reversal":
                # If method is reversal, reverse the journal entry
                frappe.msgprint(f"Reversing Journal Entry: {doc.handed}")
                handed = doc.handed
                doc.handed = ""
                journal_entry = ""
                doc.save()
                frappe.db.commit()
                reverse_journal_entry(handed)

        # Check if the 'notyet' journal entry exists
        if doc.notyet:
            if method == "reversal":
                # If method is reversal, reverse the journal entry
                frappe.msgprint(f"Reversing Journal Entry: {doc.notyet}")
                notyet = doc.notyet 
                doc.notyet = ""
                doc.save()
                frappe.db.commit()
                reverse_journal_entry(notyet)  # Call the reverse function you already have
            if method == "cancel":
                # If method is cancel, cancel the journal entry
                frappe.msgprint(f"Cancelling Journal Entry: {doc.notyet}")
                notyet = doc.notyet
                doc.notyet = ""
                doc.save()
                frappe.db.commit()
                frappe.get_doc('Journal Entry', notyet).cancel()
      
        doc.cancel()  # Cancel the transfer between branches document
        frappe.db.commit()

        frappe.msgprint("Document has been successfully updated to 'إلغاء'.")
        return {"status": "success", "message": "Document and linked Journal Entry have been processed."}

    except frappe.DoesNotExistError:
        frappe.throw("Journal Entry does not exist.")
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error Cancelling Transaction")
        frappe.throw(str(e))

###
# إلغاء الحوالة  المسلمة بعد 24 ساعة 
# يتم عبر عكس القيود المتعلقة بالحوالة
# ###
@frappe.whitelist()
def cancel_handed_transfer_after_a_day(docname, method=None):
    """
    Reverse journal entries linked to a transfer document and update its workflow state.
    """
    frappe.msgprint("cancel_handed_transfer_after_a_day is called")
    try:
        # Fetch the transfer document
        doc = frappe.get_doc('transfer between branches', docname)

        if doc.workflow_state == "ملغية":
            frappe.msgprint("This document is already cancelled.")
            return {"status": "error", "message": "This document is already cancelled."}

        try:
            # Reverse 'handed' journal entry
            if doc.handed:
                frappe.msgprint(f"Reversing Journal Entry: {doc.handed}")
                reverse_journal_entry(doc.handed)

            # Reverse 'notyet' journal entry
            if doc.notyet:
                frappe.msgprint(f"Reversing Journal Entry: {doc.notyet}")
                reverse_journal_entry(doc.notyet)

            # Update workflow state and status
            doc.db_set("workflow_state", "ملغية")  # Set to 'Cancelled' workflow state
            doc.db_set("docstatus", 2)  # Set to 'Cancelled' status
            frappe.msgprint("Transfer document workflow updated successfully.")

            frappe.db.commit()

            return {
                "status": "success",
                "message": "Journal Entries reversed and document workflow updated successfully."
            }

        except frappe.DoesNotExistError as dne_error:
            frappe.throw("One or more linked Journal Entries do not exist.")
        except Exception as je_error:
            frappe.log_error(frappe.get_traceback(), "Error in Reversing Journal Entry")
            frappe.throw(f"An error occurred while processing journal entries: {je_error}")

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in cancel_handed_transfer_after_a_day")
        frappe.throw(f"An unexpected error occurred: {e}")
        return {"status": "error", "message": str(e)}



@frappe.whitelist()
def create_journal_entry_from_canceled_transfer(docname, method):
    frappe.msgprint("create_journal_entry_from_canceled_transfer is called")
    try:
        doc = frappe.get_doc('transfer between branches', docname)

        if(doc.workflow_state == "ملغية"):
            doc.workflow_state  = "ملغية"
            doc.save()
            frappe.msgprint("This document is already cancelled.")
            return {"status": "error", "message": "This document is already cancelled."}
        
        try:
            doc.journal_entry = ""   
            if(doc.workflow_state == "غير مستلمة" and doc.notyet):
                notyet = frappe.get_doc('Journal Entry', doc.notyet)
                doc.notyet = ""
                doc.save()
                notyet.cancel()
                frappe.msgprint(f"Journal Entry {notyet.name} canceled successfully.")
            
            
            elif(doc.workflow_state == "مستلمة" and doc.handed and doc.notyet):
                handed = frappe.get_doc('Journal Entry', doc.handed)
                notyet = frappe.get_doc('Journal Entry', doc.notyet)
                doc.notyet = ""
                doc.handed = ""
                doc.save()
                notyet.cancel()
                handed.cancel()
                frappe.msgprint(f"Journal Entry(2) 1-{notyet.name} 2-{handed.name} canceled successfully.")
                
                
            doc.workflow_state = "ملغية"
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
    debit_to_liabilities = get_temp_account(doc.to_branch) #معلقات الفرع
    credit_to_account = get_main_account(doc.to_branch)# حساب الفرع الرئيسي
    journal_entry = frappe.get_doc({
        "doctype": "Journal Entry",
        "posting_date": doc.posting_date,
        "cheque_no" : doc.name,
        "cheque_date" : doc.posting_date,
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

# @frappe.whitelist()
# def create_journal_entry_from_handed_transfer(doc, method):
#     debit_to_liabilities = get_account_for_branch(doc.to_branch, 1)
#     credit_to_account = get_account_for_branch(doc.to_branch, 0)
#     journal_entry = frappe.get_doc({
#         "doctype": "Journal Entry",
#         "posting_date": doc.posting_date,
#         "accounts": [
#             {
#                 "account": debit_to_liabilities,
#                 "debit_in_account_currency": doc.amount,
#                 "credit_in_account_currency": 0,
#             },
#             {
#                 "account": credit_to_account,
#                 "debit_in_account_currency": 0,
#                 "credit_in_account_currency": doc.amount,
#             }
#         ]
#     })

#     journal_entry.custom_state = doc.docstatus
#     journal_entry.insert(ignore_permissions=True)
#     journal_entry.posting_date = doc.delivery_date
#     doc.journal_entry = journal_entry.name
#     doc.handed = journal_entry.name
    
#     doc.save()
#     frappe.db.commit()
#     journal_entry.submit()

#     frappe.publish_realtime("refresh_ui", {"docname": doc.name, "journal_entry": journal_entry.name}, user=frappe.session.user)

@frappe.whitelist()
def reverse_journal_entry(docname):
    try:
        # Fetch the original journal entry
        original_entry = frappe.get_doc("Journal Entry", docname)
        
        # Check if the journal entry has already been reversed
        if original_entry.custom_reversed_by:
            frappe.throw(f"This journal entry has already been reversed by {original_entry.custom_reversed_by}.")


        # Prepare reversed accounts
        accounts = []
        for line in original_entry.accounts:
            accounts.append({
                "account": line.account,
                "branch" : line.branch,
                "debit_in_account_currency": line.credit_in_account_currency,
                "credit_in_account_currency": line.debit_in_account_currency,
                "cost_center": line.cost_center,
                "party_type": line.party_type,
                "party": line.party
                
            })

        # Create the reversal journal entry
        reversal_entry = frappe.get_doc({
            "doctype": "Journal Entry",
            "voucher_type": original_entry.voucher_type,
            "posting_date": frappe.utils.nowdate(),
            "company": original_entry.company,
            "accounts": accounts,
            "remark": f"Reversal of Journal Entry {original_entry.name}",
            "reversal_of": original_entry.name,  # Link the reversal to the original
            "cheque_no" : original_entry.cheque_no,
            "cheque_date" : original_entry.posting_date
        })
        
        # Insert and submit the reversal entry
        reversal_entry.insert(ignore_permissions=True)
        reversal_entry.submit()

        # Update the original journal entry to reference the reversal
        original_entry.db_set("remark", "تم انعكاسة")
        original_entry.db_set("custom_reversed_by", reversal_entry.name)

        
        frappe.msgprint(f"Reversal Journal Entry {reversal_entry.name} created successfully for {original_entry.name}.")
        return {"status": "success", "message": f"Reversal Journal Entry {reversal_entry.name} created successfully."}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in Reversing Journal Entry")
        frappe.throw(f"An error occurred while reversing Journal Entry {docname}: {e}")

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
