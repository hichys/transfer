import frappe
from erpnext.accounts.doctype.journal_entry.journal_entry import JournalEntry


def custom_before_submit(doc, method):
    if doc.remark:
        # Keep only the part after "Note: "
        if "Note:" in doc.remark:
            note_part = doc.remark.split("Note:", 1)[1].strip()
            doc.remark = note_part.split("Reference #")[0].strip()
              
