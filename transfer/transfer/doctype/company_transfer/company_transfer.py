# Copyright (c) 2024, a and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import frappe
from transfer.transfer.api import (
    get_customer_account,
    create_journal_entry_preview,
    validate_linked_journal_entries,
    get_journal_entries_by_cheque,
    get_account_for_branch,
    is_posting_day_today,
    reverse_journal_entry,
)
from frappe.utils import getdate, nowdate
from frappe import _


class companytransfer(Document):
    def on_update_after_submit(self):
        if self.delivery_date and self.posting_date:
            if getdate(self.delivery_date) < getdate(self.posting_date):
                frappe.throw(_("تاريخ التسليم يجيب ان يكون اكبر من تاريخ الحوالة"))

    def validate(self):
        if self.delivery_date and self.posting_date:
            if getdate(self.delivery_date) < getdate(self.posting_date):
                frappe.throw(_("تاريخ التسليم يجيب ان يكون اكبر من تاريخ الحوالة"))

    # def after_save(doc, method):
    # 	if doc.docstatus == 1:  # Document is submitted
    # 		frappe.publish_realtime(
    # 			"msgprint",
    # 			{"message": _("Document has been updated. Please reload."), "alert": 1},
    # 			user=frappe.session.user
    # 		)
    def create_company_transfer():
        frappe.msgprint("Company Transfer Created")

    def before_cancel(self):
        pass

    def on_submit(self):
        if self.status == "غير مسجلة":
            handle_creation(self.name, "submit")

    def on_cancel(self):
        if self.docstatus == 2:
            self.status = "ملغية"

    def before_insert(self):
        if self.our_profit + self.other_party_profit > self.profit:
            frappe.throw("الرجاء التاكد من قيمة العمولة")

    def before_save(self):
        # if not self.journal_entry:
        # 	create_journal_entry(self)
        pass

    def after_cancel(self):
        self.status = "ملغية"
        frappe.msgprint("تم الغاء العملية")

    def after_cancel(self):
        if self.docstatus == 2:  # Check if the document is in draft state
            # Cancel directly without journal entry handling
            self.status = "ملغية"

    def on_cancel(self):

        try:

            # Fetch the journal entry linked to the current document
            journal_entries = frappe.get_all(
                "Journal Entry", filters={"cheque_no": self.name}
            )
            if not journal_entries:
                frappe.msgprint(
                    f"No journal entry found for cheque number: {self.name}"
                )
                return

            # Load the first journal entry found
            je = frappe.get_doc("Journal Entry", journal_entries[0].name)
            try:
                # Get today's date and the posting date of the journal entry
                today = getdate(nowdate())
                posting_date = getdate(self.posting_date)

                if posting_date == today:
                    # If the journal entry was created today, cancel it
                    je.cancel()
                    if not validate_linked_journal_entries(self.name):
                        frappe.throw("ERRROR on_cancel CODE COM888")
                    frappe.msgprint(f"Journal Entry {je.name} has been cancelled.")
                else:
                    # If the journal entry is older than today, reverse it
                    reverse_journal_entry(je, self.name)
                    frappe.msgprint(f"Journal Entry {je.name} has been reversed.")

                    # Update the status and docstatus of the document

                    frappe.msgprint("Document canceled successfully from Draft state.")

            except Exception as journal_error:
                frappe.log_error(frappe.get_traceback(), "Error handling Journal Entry")
                frappe.throw(
                    f"An error occurred while processing the Journal Entry: {str(journal_error)}"
                )
        except Exception as main_error:
            frappe.log_error(frappe.get_traceback(), "Error in on_cancel method")
            frappe.throw(f"An error occurred during cancellation: {str(main_error)}")


@frappe.whitelist()
def get_branch():
    return frappe.get_cached_doc("Transfer Setting").main_branch


def getSelf(docname):
    return frappe.get_doc("company transfer", docname)


# @frappe.whitelist()
# def handle_creation(docname, method="submit"):


#     doc = getSelf(docname)
#     doc.status = "غير مستلمة"
#     doc.submit()
#     create_journal_entry(doc)
#     frappe.db.commit()
#     frappe.publish_realtime("doc_update", {"docname": docname, "status": doc.status})
@frappe.whitelist()
def handle_creation(docname, method="submit"):
    doc = frappe.get_doc("company transfer", docname)
    doc.status = "غير مستلمة"
    doc.submit()
    create_journal_entry(doc)
    frappe.db.commit()
    return {"status": "success"}


@frappe.whitelist()
def create_journal_entry(self):
    debit = self.amount
    credit = self.execution_amount
    our_profit = self.our_profit
    profit_account = get_account_for_branch(self.branch, 1)  # حساب العمولات
    branch = self.branch
    other_party_profit = self.other_party_profit
    from_party_name = self.from_company
    to_party_name = self.to_company
    try:
        journal_entries = frappe.get_all(
            "Journal Entry", filters={"cheque_no": self.name}
        )
        if journal_entries:
            frappe.log_error(frappe.get_traceback(), "Error in Creating Journal Entry")
            frappe.throw(f"الحوالة مسجلة مسبقا {journal_entries[0].name}")
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in Creating Journal Entry")
        frappe.throw(f"An error occurred while creating the Journal Entry: {str(e)}")
    try:
        # Validate that the required fields are provided

        if not (debit and credit and profit_account):
            frappe.throw("Debit, Credit, and Profit Account must be specified.")

        if self.from_type == "Branch":
            accounts = [
                {
                    "account": self.debit,  # Specify the debit account
                    "branch": branch,
                    "party_type": "",
                    "party": "",
                    "debit_in_account_currency": self.amount + self.profit,
                    "credit_in_account_currency": 0,
                },
                {
                    "account": get_customer_account(),  # Specify the credit account
                    "branch": branch,
                    "party_type": "Customer",
                    "party": to_party_name,
                    # "is_advance":"Yes",
                    "debit_in_account_currency": 0,
                    "credit_in_account_currency": self.execution_amount
                    - self.our_profit,
                },
            ]
        else:
            # Prepare accounts for the Journal Entry
            accounts = [
                {
                    "account": get_customer_account(),  # Specify the debit account
                    "branch": branch,
                    "party_type": "Customer",
                    "party": from_party_name,
                    "debit_in_account_currency": credit,
                    "credit_in_account_currency": 0,
                },
                {
                    "account": get_customer_account(),  # Specify the credit account
                    "branch": branch,
                    "party_type": "Customer",
                    "party": to_party_name,
                    "debit_in_account_currency": 0,
                    "credit_in_account_currency": debit + other_party_profit,
                },
            ]
        # Add an entry for out_proft if not 0
        if our_profit != 0:
            accounts.append(
                {
                    "account": profit_account,
                    "branch": branch,
                    "debit_in_account_currency": 0,
                    "credit_in_account_currency": our_profit,
                }
            )
        # Add an entry for other_party_profit if not 0
        # if other_party_profit != 0:
        # 	accounts.append({
        # 		"account": self.credit,
        # 		"branch": branch,
        # 		"party_type": "Customer",
        # 		"party": to_party_name,
        # 		"debit_in_account_currency": 0,
        # 		"credit_in_account_currency": other_party_profit,
        # 	})

        # Construct the Journal Entry document
        journal_entry = frappe.get_doc(
            {
                "doctype": "Journal Entry",
                "voucher_type": "Journal Entry",
                "posting_date": frappe.utils.nowdate(),
                "accounts": accounts,
                "mode_of_payment": "Cash",
                "cheque_no": self.name,
                "cheque_date": frappe.utils.nowdate(),
                "user_remark": self.whatsapp_desc,
            }
        )

        # Save and Submit the Journal Entry
        journal_entry.insert(ignore_permissions=True)
        journal_entry.submit()
        self.journal_entry = journal_entry.name

        # frappe.msgprint(f"Journal Entry {journal_entry.name} created successfully.")
        self.status = "غير مستلمة"
        return {"status": "success", "journal_entry": journal_entry.name}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in Creating Journal Entry")
        frappe.throw(f"An error occurred while creating the Journal Entry: {str(e)}")


@frappe.whitelist()
def reverse_journal_entry(self, docname):
    try:
        # Fetch the original journal entry using the 'cheque_no' as the reference to self.name
        journal_entry = frappe.get_doc("Journal Entry", self.name)
        if journal_entry:
            # Get the original journal entry

            # Prepare reversed accounts by swapping the debit and credit values
            reversed_accounts = []
            for account in journal_entry.accounts:
                reversed_account = {
                    "account": account.account,
                    "branch": account.branch,
                    "party_type": account.party_type,
                    "party": account.party,
                    "debit_in_account_currency": account.credit_in_account_currency,
                    "credit_in_account_currency": account.debit_in_account_currency,
                }
                reversed_accounts.append(reversed_account)

            # Create the reversed journal entry
            reversed_je = frappe.get_doc(
                {
                    "doctype": "Journal Entry",
                    "voucher_type": journal_entry.voucher_type,
                    "posting_date": nowdate(),
                    "company": journal_entry.company,
                    "accounts": reversed_accounts,
                    "mode_of_payment": "Cash",  # Adjust as per your requirements
                    "cheque_no": f"{docname}",
                    "cheque_date": nowdate(),
                    "reversal_of": journal_entry.name,
                    "user_remark": journal_entry.user_remark,
                }
            )

            # Insert and submit the reversed journal entry
            reversed_je.insert(ignore_permissions=True)
            reversed_je.submit()

            # edit original journal entry
            journal_entry.custom_reversed_by = reversed_je.name
            journal_entry.save()
            frappe.db.commit()
            frappe.msgprint(
                f"Journal Entry {reversed_je.name} has been reversed successfully."
            )

            return {"status": "success", "journal_entry": reversed_je.name}

        else:
            frappe.throw(
                f"No journal entry found for the provided cheque number: {self.name}"
            )

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in Reversing Journal Entry")
        frappe.throw(f"An error occurred while reversing the Journal Entry: {str(e)}")


## ui buttons


@frappe.whitelist()
def handle_recived_transfer(docname, method):
    # Parse the doc JSON string into a Python object
    doc = frappe.get_doc("company transfer", docname)

    if doc.docstatus == 1:  # Check if the document is submitted
        if doc.status == "غير مستلمة":
            doc.status = "مستلمة"
            # frappe.msgprint(f"Document {docname} is in the status: {doc.status}")
            doc.save()
            frappe.db.commit()

        else:
            frappe.msgprint("No action required.")
    else:
        frappe.throw("The document is not submitted.")


@frappe.whitelist()
def handle_cancel_transfer(docname, method="cancel"):
    # Parse the doc JSON string into a Python object
    doc = frappe.get_doc("company transfer", docname)

    # frappe.msgprint("caling handle_cancel_transfer;")
    if doc.docstatus == 1:  # Check if the document is submitted
        if is_posting_day_today(doc.posting_date):
            # frappe.msgprint(f"attempt to cancel {doc.docstatus}")
            doc.status = "ملغية"
            doc.save()
            doc.docstatus = 2
            doc.cancel()
            frappe.db.commit()
        else:
            handel_reverse(doc)
            doc.status = "ملغية"
            doc.docstatus = 2
            doc.save()
            frappe.db.commit()

    else:
        if method == "cancel":
            frappe.throw("The document is not submitted.")


@frappe.whitelist()
def handel_reverse(doc):
    journal_entry = get_journal_entries_by_cheque(doc)
    reverse_journal_entry(self=journal_entry[0], docname=doc.name)


# wrapper to call api function and get branch account


# الحساب الرئيسي
@frappe.whitelist()
def get_main_account(branch):
    return get_account_for_branch(branch, 0)


@frappe.whitelist()
# معلقات
def get_profit_account(branch):
    return get_account_for_branch(branch, 1)


# ارباح
@frappe.whitelist()
def get_temp_account(branch):
    return get_account_for_branch(branch, 2)
