# Copyright (c) 2024, a and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from transfer.transfer.api import get_account_for_branch
from .create_journal_entery import *
 

class transferbetweenbranches(Document):
	#الاحداث البتحصل لمن الدوك تتحفظ لاول مرة
	# القيد الافتتاحي للعملية
	def before_cancel(self):
		frappe.msgprint("before cancel")
	def on_trash(self):
		frappe.msgprint("cancel")
	def after_insert(self):
		# Trigger your custom logic here
		if self.workflow_state == "معلقة" and not self.notyet:
			debit  = get_account_for_branch(branch_name=self.from_branch, account_index=0)
			credit = get_account_for_branch(branch_name=self.to_branch, account_index=1)
			#frappe.msgprint(f"debit : {debit} \n credit : {credit}")
			self.debit = debit
			self.credit = credit	
			create_journal_entry_from_pending_transfer(self,method="submit")
			#transfer_created()

		# Example: Perform an action, like creating another document
		#self.create_related_doc()
		
	def on_change(self):
		# Check if the workflow_state has changed
		frappe.msgprint("on change :"+self.workflow_state)
			# Trigger custom logic based on the new workflow state
		if self.workflow_state == "تم التسليم" and not self.handed:
			debit  = get_account_for_branch(branch_name=self.to_branch, account_index=1)
			credit = get_account_for_branch(branch_name=self.to_branch, account_index=0)
			#frappe.msgprint(f"debit : {debit} \n credit : {credit}")
			self.debit = debit
			self.credit = credit	
			create_journal_entry_from_handed_transfer(self,method="submit")
			#transfer_delievred()
		elif self.workflow_state == "إلغاء" and not self.canceld_journal_entry:
			debit  = get_account_for_branch(branch_name=self.to_branch, account_index=1)
			credit = get_account_for_branch(branch_name=self.from_branch, account_index=0)
			frappe.msgprint(f"debit : {debit} \n credit : {credit}")
			self.debit = debit
			self.credit = credit
			create_journal_entry_from_canceled_transfer(self,method="submit")
				
				
	def on_update(self):
		print("on update called")
		self.transfer()         
	def on_submit(self):
		print("on submit	 called")
		#self.transfer()		
		
	def on_save(self):
		frappe.msgprint(f"تم تسجيل الحوالة في المنظومة بنجاح")
	def transfer(self):
		# Directly access the fields in the current document instance (self)
		amount = self.amount  # 'amount' is the field in your document
		commission_amount = self.profit  # Assuming 'profit' is a field in this document
		debit = self.debit  # Assuming 'debit' is a field in this document
		credit = self.credit  # Assuming 'credit' is a field in this document
		selected_status = self.status  # Replace 'status' with the fieldname of your select field
		
		# Print values for debugging
		print(f"Selected status: {selected_status} amount: {amount}, commission amount: {commission_amount}, debit: {debit}, credit: {credit}")
		
		# Uncomment and implement your journal entry function if needed
		#on_status_change(docname=self.name, from_branch= debit, to_branch= credit, selected_status=self.status)
  
import frappe

@frappe.whitelist()
def force_cancel_document(docname):
    try:
        # Fetch the document
        doc = frappe.get_doc('transfer between branches', docname)
        
        # Check if the document can be canceled
        if doc.docstatus == 1:
            # Cancel the document
            doc.cancel()
            frappe.db.commit()
            return {"status": "success", "message": f"Document {docname} has been canceled successfully."}
        else:
            return {"status": "fail", "message": f"Document {docname} is not in a state that can be canceled."}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in force_cancel_document")
        frappe.throw(f"An error occurred while canceling the document: {str(e)}")
@frappe.whitelist()
def on_status_change(doc,method):
    pass
	# doc = frappe.get_doc('transfer between branches', docname)
	# # Add custom logic here based on the new status
	# doc.status = new_status
	# if new_status == "تم التسليم" :
	# 	debit  = get_account_for_branch(branch_name=to_branch, account_index=1)
	# 	credit = get_account_for_branch(branch_name=to_branch, account_index=0)
	# 	frappe.msgprint(f"debit : {debit} \n credit : {credit}")
	# 	doc.debit = debit
	# 	doc.credit = credit	
	# 	create_journal_entry_from_handed_transfer(doc,method="submit")
	# elif new_status == "لم تسلم":
	# 	debit  = get_account_for_branch(branch_name=from_branch, account_index=0)
	# 	credit = get_account_for_branch(branch_name=to_branch, account_index=1)
	# 	frappe.msgprint(f"debit : {debit} \n credit : {credit}")
	# 	doc.debit = debit
	# 	doc.credit = credit	
	# 	create_journal_entry_from_pending_transfer(doc,method="submit")
	# elif new_status == "راجعه او ملغية":
	# 	debit  = get_account_for_branch(branch_name=to_branch, account_index=1)
	# 	credit = get_account_for_branch(branch_name=from_branch, account_index=0)
	# 	frappe.msgprint(f"debit : {debit} \n credit : {credit}")
	# 	doc.debit = debit
	# 	doc.credit = credit
	# 	create_journal_entry_from_canceled_transfer(doc,method="submit")
	# doc.save()
	# Example: Update another field or trigger another action
	#doc.db_set('last_status_update', frappe.utils.now())

# لم تسلم بعد
def create_journal_entry_from_pending_transfer(doc, method):
	# Creating a Journal Entry
	if doc.journal_entry and doc.previous_status =="" :
		frappe.msgprint(f"Cant do that")
		return
	
	commision = doc.profit/2
	debit_with_commision = doc.amount + doc.profit
	to_profit_accunt = get_account_for_branch(doc.from_branch,2)
	from_profit_accunt = get_account_for_branch(doc.to_branch,2)
	
	if commision != 0 :
		journal_entry = frappe.get_doc({
		"doctype": "Journal Entry",
			"posting_date": doc.posting_date,
			"mode_of_payment": "Cash",
			"accounts": [
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
				},
				{
					"account": to_profit_accunt,
					"branch": doc.from_branch,
					"debit_in_account_currency": 0,
					"credit_in_account_currency": commision,
				},
				{
					"account": from_profit_accunt,
					"branch": doc.to_branch,
					"debit_in_account_currency": 0,
					"credit_in_account_currency": commision,
				}
			]
		})
	elif commision == 0:
		journal_entry = frappe.get_doc({
		"doctype": "Journal Entry",
			"posting_date": doc.posting_date,
			"mode_of_payment": "Cash",
			"accounts": [
				{
					"account": doc.debit,
					"branch" : doc.from_branch,
					"debit_in_account_currency": debit_with_commision,
					"credit_in_account_currency": 0,
				},
				{
					"account": doc.credit,
					"branch" : doc.to_branch,
					"debit_in_account_currency": 0,
					"credit_in_account_currency": doc.amount,
				}
			]
		})

	# Save the Journal Entry
	journal_entry.insert(ignore_permissions=True)
	frappe.db.commit()
	

	# Link the created journal entry to the current document
	#لنك للجورنال انتري من التحويل بين الفروع
	doc.journal_entry = journal_entry.name
	doc.journal_entry_link = f'<a href="/app/journal-entry/{journal_entry.name}" target="_blank">{journal_entry.name}</a>'
	doc.notyet =  journal_entry.name
	doc.save()
	
	journal_entry.custom_state = doc.status
	journal_entry.submit()
	# Optionally, submit the Journal Entry
	frappe.publish_realtime("refresh_ui", {"docname": doc.name, "journal_entry": journal_entry.name}, user=frappe.session.user)

	
	#frappe.msgprint(f"Journal Entry {journal_entry.name} created and linked to the Transfer Between Branches document.")


#الحوالات الراجعه او الملغية
# يعكس القيد في حالة كانت الحوالة "لم تستلم" كالاتي:
def create_journal_entry_from_canceled_transfer(doc, method):
	# Creating a Journal Entry
	
	commision = doc.profit/2
	debit_with_commision = doc.amount + doc.profit
	to_profit_accunt = get_account_for_branch(doc.from_branch,2)
	from_profit_accunt = get_account_for_branch(doc.to_branch,2)
	journal_entry = frappe.get_doc({
	"doctype": "Journal Entry",
		"posting_date": doc.posting_date,
		"accounts": [
			{
				"account": doc.debit,
				"branch": doc.from_branch,
				"debit_in_account_currency": 0,
				"credit_in_account_currency": debit_with_commision,
			},
			{
				"account": doc.credit,
				"branch": doc.to_branch,
				"debit_in_account_currency": doc.amount,
				"credit_in_account_currency": 0,
			},
			{
				"account": to_profit_accunt,
				"branch": doc.from_branch,
				"debit_in_account_currency": commision,
				"credit_in_account_currency": 0,
			},
			{
				"account": from_profit_accunt,
				"branch": doc.to_branch,
				"debit_in_account_currency": commision,
				"credit_in_account_currency": 0,
			}
		]
	})
	journal_entry.custom_transaction =  doc.name
	journal_entry.custom_state = doc.status
	# Save the Journal Entry
	journal_entry.insert(ignore_permissions=True)
	
	frappe.db.commit()
	journal_entry.submit()

	# Link the created journal entry to the current document
	doc.journal_entry = journal_entry.name
	doc.canceld_journal_entry = journal_entry.name
	
	doc.save()
	# Optionally, submit the Journal Entry
	frappe.publish_realtime("refresh_ui", {"docname": doc.name, "journal_entry": journal_entry.name}, user=frappe.session.user)


	#frappe.msgprint(f"Journal Entry {journal_entry.name} created and linked to the Transfer Between Branches document.")


#الحوالات المستلمه
#في حالة الحوالة المستلمة , تتحول القيمه المستلمه
#  من الخزنه المعلقة للمستلم الي الخزنة الريسة
def create_journal_entry_from_handed_transfer(doc, method):
	# Creating a Journal Entry
	debit_to_laibites = get_account_for_branch(doc.to_branch,1)
	credit_to_account = get_account_for_branch(doc.to_branch,0)
	journal_entry = frappe.get_doc({
	"doctype": "Journal Entry",
		"posting_date": doc.posting_date,
		"accounts": [
			{
				"account": debit_to_laibites,
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

	# Save the Journal Entry
	
	journal_entry.custom_transaction =  doc.name
	journal_entry.custom_state = doc.status
	journal_entry.insert(ignore_permissions=True)
	journal_entry.posting_date = doc.delivery_date
	frappe.db.commit()
	journal_entry.submit()

	# Link the created journal entry to the current document
	doc.journal_entry = journal_entry.name
	doc.handed = journal_entry.name
	doc.handed = doc.delivery_date
	doc.save()
	# Optionally, submit the Journal Entry
	frappe.publish_realtime("refresh_ui", {"docname": doc.name, "journal_entry": journal_entry.name}, user=frappe.session.user)


	#frappe.msgprint(f"awad Journal Entry {journal_entry.name} created and linked to the Transfer Between Branches document.")

