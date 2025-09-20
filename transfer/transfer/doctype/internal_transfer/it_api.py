import frappe
from transfer.transfer.api import get_journal_entries_by_cheque,reverse_journal_entry
import frappe

def it_cancel_journal_entries(doc):
    # Fetch the journal entries related to the custom document by 'cheque_no'
    journal_entries = get_journal_entries_by_cheque(doc)
    
    # Check if there are any journal entries to cancel
    if not journal_entries:
        frappe.throw("No journal entries found to cancel.")
    
    # Initialize a flag to track if all journal entries were canceled successfully
    all_canceled = True
    
    # Loop through each journal entry and cancel it
    for journal_entry in journal_entries:
        try:
            # Fetch the Journal Entry document
            je_doc = frappe.get_doc('Journal Entry', journal_entry['name'])
            
            # Check if the Journal Entry can be canceled (you can add more conditions here)
            if je_doc.docstatus == 1:  # Only cancel if it is submitted
                je_doc.cancel()
                # frappe.msgprint(f"Journal Entry {je_doc.name} canceled successfully.")
            else:
                # If it cannot be canceled (e.g., already canceled), mark it as failed
                all_canceled = False
                frappe.msgprint(f"Journal Entry {je_doc.name} is already canceled or not in a cancelable state.")
        
        except Exception as e:
            # If there's an error canceling the journal entry, mark it as failed
            all_canceled = False
            frappe.msgprint(f"Failed to cancel Journal Entry {journal_entry['name']}: {str(e)}")
    
    # After attempting to cancel all entries, check if all were canceled
    if not all_canceled:
        frappe.throw("Not all journal entries were canceled successfully.")
        return False
    
    return True


def it_reverse_journal_entries(doc):
    # frappe.msgprint("Reversing")
    # Fetch the journal entries related to the custom document by 'cheque_no'
    journal_entries = get_journal_entries_by_cheque(doc)

    # Check if there are any journal entries to cancel
    if not journal_entries:
        frappe.throw("No journal entries found to reverse.")

    # Initialize a flag to track if all journal entries were canceled successfully
    all_canceled = True

    # Loop through each journal entry and cancel it
    for journal_entry in journal_entries:
        try:
            # Fetch the Journal Entry document
            je_doc = frappe.get_doc('Journal Entry', journal_entry['name'])

            # Check if the Journal Entry can be canceled (you can add more conditions here)
            # Only cancel if it is submitted and its not revesed
            if je_doc.docstatus == 1 and not je_doc.custom_reversed_by: 
                reverse_journal_entry(je_doc,doc.name)
                # frappe.msgprint(f"Journal Entry {je_doc.name} reversed successfully.")
            else:
                # If it cannot be canceled (e.g., already canceled), mark it as failed
                all_canceled = False
                # frappe.msgprint(f"Journal Entry {je_doc.name} is already reversed or not in a reverseable state.")

        except Exception as e:
            # If there's an error canceling the journal entry, mark it as failed
            all_canceled = False
            frappe.msgprint(f"Failed to reverse Journal Entry {journal_entry['name']}: {str(e)}")

    # After attempting to cancel all entries, check if all were canceled
    if not all_canceled:
        frappe.throw("Not all journal entries were reversed successfully.")
        return False

    return True
