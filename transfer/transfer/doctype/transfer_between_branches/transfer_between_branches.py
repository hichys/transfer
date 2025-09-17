# Copyright (c) 2024, a and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from transfer.transfer.api import get_document,get_company_main_account, get_journal_entries_by_cheque, get_main_account,get_temp_account,get_profit_account,validate_linked_journal_entries
from .create_journal_entery import *
from datetime import datetime, timedelta
from frappe.utils import getdate, nowdate
from erpnext.accounts.utils import get_balance_on
from frappe.model.workflow import apply_workflow


class transferbetweenbranches(Document):
	def on_update_after_submit(self):
		if self.delivery_date and self.posting_date:
			if getdate(self.delivery_date) < getdate(self.posting_date):
				frappe.throw(_("تاريخ التسليم يجيب ان يكون اكبر من تاريخ الحوالة"))

	def validate(self):
		if self.delivery_date and self.posting_date:
			if getdate(self.delivery_date) < getdate(self.posting_date):
				frappe.throw(_("تاريخ التسليم يجيب ان يكون اكبر من تاريخ الحوالة"))
	def before_cancel(self):
		validate_linked_journal_entries(self.name)
	def on_cancel(self):
		pass
	def after_insert(self):
		pass
	  # Save the previous state when the document is loaded

	def on_change(self):
		
		# check previous state
		if(self.get_doc_before_save() and not self.get_doc_before_save().workflow_state == "مستلمة"):
			if self.workflow_state == "مستلمة" and not self.handed:
				frappe.msgprint("تم التسليم **3434***")
				create_journal_entry_from_handed_transfer(self, method="submit")


	def on_update(self):
		# frappe.msgprint("on update called")
		pass
		

	def on_submit(self):
		if self.workflow_state == "غير مستلمة" and not self.notyet:
			debit = get_main_account(self.from_branch)
			credit = get_temp_account(self.to_branch)
			self.debit = debit
			self.credit = credit
			create_journal_entry_from_pending_transfer(self, method="submit")

	def on_save(self):
		frappe.msgprint("تم تسجيل الحوالة في المنظومة بنجاح")

#delete the doctype and its linked journal entries fillters cheque_no
@frappe.whitelist()
def delete_doc_with_links(docname):
	doc = frappe.get_doc("transfer between branches", docname)
	frappe.msgprint(f"Deleting document: {docname}")
	if doc.workflow_state != "ملغية":
		frappe.throw(_("Only documents in 'ملغيه' state can be deleted."))

	journal_entries = frappe.get_all("Journal Entry", filters={"cheque_no": docname})
	for je in journal_entries:
		je_doc = frappe.get_doc("Journal Entry", je.name)

		if je_doc.docstatus == 1:
			je_doc.cancel()
			je_doc.reload()

		if je_doc.docstatus == 2:
			je_doc.delete()

	doc.delete()
	frappe.db.commit()

	if frappe.db.exists("transfer between branches", docname):
		frappe.throw(_("Failed to delete the document."))

	return "Deleted successfully"

@frappe.whitelist()
def manual_submit(docname):
	try:
		doc = frappe.get_doc("transfer between branches", docname)
		doc.submit()
		frappe.db.commit()
		return "success"
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Error 6695 in manual_submit")

@frappe.whitelist()
def test(docname,method="cancel"):
	try:
		# Check if the document is from the day before
		if not is_document_from_yesterday(docname):
			handel_cancelation(docname,method="cancel")
		else:
			handel_cancelation(docname,method="reversal")
	
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Error 987 in handel_cancelation")
		frappe.throw(str(e))


def is_document_from_yesterday(docname):
	"""
	Check if the document was created the day before.
	"""
	try:
		doc = frappe.get_doc("transfer between branches", docname)
		posting_date = doc.posting_date.date()  # Date part of the creation datetime
		
		# Get yesterday's date
		yesterday = (datetime.today() - timedelta(days=1)).date()
		print(yesterday)
		print("===================should reverse======================")
		return posting_date == yesterday
	except frappe.DoesNotExistError:
		frappe.throw(f"Document {docname} does not exist.")
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Error in is_document_from_yesterday")
		frappe.throw(str(e))


@frappe.whitelist()
def handel_canceled_docs(docname, method):
	frappe.msgprint("create_journal_entry_from_canceled_transfer is called")
	try:
		doc = frappe.get_doc('transfer between branches', docname)

		if(doc.docstatus == 2):
			
			if doc.notyet:
				notyet_entry = frappe.get_doc('Journal Entry', doc.notyet)
				notyet_entry.cancel()
				frappe.msgprint(f"Journal Entry {notyet_entry.name} canceled successfully.")

			if doc.handed:
				handed_entry = frappe.get_doc('Journal Entry', doc.handed)
				handed_entry.cancel()
				frappe.msgprint(f"Journal Entry {handed_entry.name} canceled successfully.")
			frappe.msgprint("this document 1111has been canceled")
			return

		try:
			#doc.journal_entry = ""   #
			if(doc.workflow_state == "غير مستلمة" and doc.notyet):
				notyet = frappe.get_doc('Journal Entry', doc.notyet)
				doc.notyet = ""
				doc.save(ignore_permissions=True)
				notyet.cancel()
				frappe.msgprint(f"Journal Entry {notyet.name} canceled successfully.")
			
			
			elif(doc.workflow_state == "مستلمة" and doc.handed and doc.notyet):
				handed = frappe.get_doc('Journal Entry', doc.handed)
				notyet = frappe.get_doc('Journal Entry', doc.notyet)
				doc.notyet = ""
				doc.handed = ""
				doc.save(ignore_permissions=True)
				notyet.cancel()
				handed.cancel()
				frappe.msgprint(f"Journal Entry(2) 1-{notyet.name} 2-{handed.name} canceled successfully.")
				
			doc.db_set("workflow_state", "ملغية")  # Set to 'Cancelled' workflow state
			doc.db_set("docstatus", 2)  # Set to 'Cancelled' status
			frappe.msgprint("Transfer document workflow updated successfully.")
			# Update the workflow state explicitly
			# Cancel the document

			if doc.docstatus != 2 and doc.workflow_state != "ملغية" :
				frappe.throw("cant cancel yet")
			
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
def handel_cancelation(docname, method):
	# if method == "reversal": revese it
	# else if method == cancel then cancel it

	if method == "reversal":
		handel_reversal(docname, method="reversal")
	elif method == "cancel":
		handel_canceled_docs(docname, method="cancel")
	else:
		frappe.throw("Invalid method. Please provide a valid method.")


@frappe.whitelist()
def create_journal_entry_from_pending_transfer(doc, method):
	# show alert
	# frappe.msgprint("create_journal_entry_from_pending_transfer is called")

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
		"cheque_date" : doc.posting_date,
		"user_remark": doc.whatsapp_desc
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

		# frappe.msgprint(doc.journal_entry_link)
		# frappe.msgprint(f"Journal Entry {journal_entry.name} created and linked to the Transfer Between Branches document.")
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Error Creating Journal Entry")
		frappe.throw(f"An error occurred while creating the Journal Entry: {e}")    


@frappe.whitelist()
def handel_reversal(docname, method):
	frappe.msgprint("handel_reversal is called")
	try:
		# Fetch the document
		doc = frappe.get_doc('transfer between branches', docname)
		if not doc:
			frappe.throw("الرجاء انشاء الحوالة اولا")

		# Ensure the transaction is in a state where it can be canceled or reversed
		if method not in ["reversal", "cancel"]:
			frappe.throw(_("Invalid method. Please provide 'reversal' or 'cancel'."))
		
		if doc.workflow_state == "غير مسجلة":
			frappe.throw("الحوالة غير مسجلة")

		# Handling the handed journal entry
		if doc.handed:
			if method == "reversal":
				frappe.msgprint(f"Reversing Handed Journal Entry: {doc.handed}")
				handed = doc.handed
				doc.handed = ""
				reverse_journal_entry(handed,doc.posting_date)  # Reverse the journal entry
				frappe.msgprint(f"Handed Journal Entry {handed} has been reversed")

		# Handling the notyet journal entry
		if doc.notyet:
			if method == "reversal":
				frappe.msgprint(f"Reversing NotYet Journal Entry: {doc.notyet}")
				notyet = doc.notyet
				doc.notyet = ""
				reverse_journal_entry(notyet,doc.posting_date)  # Reverse the journal entry
				frappe.msgprint(f"NotYet Journal Entry {notyet} has been reversed")
			if method == "cancel":
				frappe.msgprint(f"Cancelling NotYet Journal Entry: {doc.notyet}")
				notyet = doc.notyet
				doc.notyet = ""
				# Cancel the journal entry
				journal_entry = frappe.get_doc('Journal Entry', notyet)
				journal_entry.cancel()
				handed = doc.handed
				doc.handed = ""
				# Cancel the journal entry
				handed = frappe.get_doc('Journal Entry', handed)
				handed.cancel()
				doc.workflow_state = "ملغية"
				doc.save()
				
				frappe.msgprint(f"NotYet Journal Entry {notyet} has been canceled")

		# Cancel the transfer document
		doc.db_set("workflow_state", "ملغية")  # Set to 'Cancelled' workflow state
		doc.db_set("docstatus", 2)  # Set to 'Cancelled' status
		frappe.msgprint("Transfer document workflow updated successfully.")

		frappe.db.commit()  # Commit changes to the database after all actions
		frappe.msgprint("Document has been successfully updated to 'إلغاء'.")
		
		return {"status": "success", "message": "Document and linked Journal Entries have been processed."}

	except frappe.DoesNotExistError:
		frappe.throw("The specified document or Journal Entry does not exist.")
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Error Cancelling Transaction")
		frappe.throw(f"Error 002: {str(e)}")


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
			# frappe.msgprint("This document is already cancelled.")
			return {"status": "error", "message": "This document is already cancelled."}

		try:
			# Reverse 'handed' journal entry
			if doc.handed:
				frappe.msgprint(f"Reversing Journal Entry: {doc.handed}")
				reverse_journal_entry(doc.handed,doc.posting_date)

			# Reverse 'notyet' journal entry
			if doc.notyet:
				frappe.msgprint(f"Reversing Journal Entry: {doc.notyet}")
				reverse_journal_entry(doc.notyet,doc.posting_date)

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
		frappe.log_error(frappe.get_traceback(), "Error999 in cancel_handed_transfer_after_a_day")
		frappe.throw(f"An unexpected error occurred: {e}")
		return {"status": "error", "message": str(e)}


	

@frappe.whitelist()
def create_journal_entry_from_handed_transfer(doc, method):
 
	doc = get_document(doc,"transfer between branches")

	debit_to_liabilities = get_temp_account(doc.to_branch) #معلقات الفرع
	credit_to_account = get_main_account(doc.to_branch)# حساب الفرع الرئيسي

	if(doc.check_tslmfrommain): 
		#validate to_branch is actually "العالمية الفرناج"
		settings = frappe.get_cached_doc("Transfer Setting")
		if doc.to_branch == settings.main_branch:
			credit_to_account = get_company_main_account()
			from_account_balance = get_balance_on(credit_to_account,date=nowdate())
			if from_account_balance < doc.amount:
				frappe.throw(f"الرصيد غير كافي في الحساب. الرصيد الحالي: {from_account_balance}, المبلغ المطلوب: {doc.amount}")
		else :
			frappe.throw("التسليم من الخزنة الرئسية غير متوفر لهذا الفرع")
	journal_entry = frappe.get_doc({
		"doctype": "Journal Entry",
		"posting_date": doc.posting_date,
		"cheque_no" : doc.name,
		"cheque_date" : doc.posting_date,
		"user_remark" : doc.whatsapp_desc,
		"accounts": [
			{
				"account": debit_to_liabilities,
				"branch":doc.to_branch,
				"debit_in_account_currency": doc.amount,
				"credit_in_account_currency": 0,
			},
			{
				"account": credit_to_account,
				"branch" :doc.to_branch,
				"debit_in_account_currency": 0,
				"credit_in_account_currency": doc.amount,
			}
		]
	})

	journal_entry.custom_state = doc.docstatus
	journal_entry.insert(ignore_permissions=True)
	journal_entry.posting_date = doc.delivery_date
	#doc.journal_entry = journal_entry.name
	doc.handed = journal_entry.name
	
	doc.save()
	frappe.db.commit()
	journal_entry.submit()

	frappe.publish_realtime("refresh_ui", {"docname": doc.name, "journal_entry": journal_entry.name}, user=frappe.session.user)

@frappe.whitelist()
def reverse_journal_entry(docname,reversal_date):
	try:
		# Fetch the original journal entry
		original_entry = frappe.get_doc("Journal Entry", docname)
		
		# Check if the journal entry has already been reversed
		if original_entry.custom_reversed_by:
			frappe.throw(f"ERORR CODE 777 :This journal entry has already been reversed by {original_entry.custom_reversed_by} .")


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
				"party": line.party,
				"branch": line.branch
				
			})

		# Create the reversal journal entry
		reversal_entry = frappe.get_doc({
			"doctype"	  : "Journal Entry",
			"voucher_type": original_entry.voucher_type,
			"posting_date": reversal_date,
			"company"     : original_entry.company,
			"accounts"    : accounts,
			"reversal_of" : original_entry.name,  # Link the reversal to the original
			"cheque_no"   : original_entry.cheque_no,
			"cheque_date" : original_entry.posting_date,
			"user_remark"     : original_entry.user_remark
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
		frappe.throw(f"An error 888 occurred while reversing Journal Entry {docname}: {e}")

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
