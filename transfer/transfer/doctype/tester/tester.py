# Copyright (c) 2024, a and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class tester(Document):
	def on_update(self):
		frappe.msgprint("asd")
		
		if self.docstatus == 2:
			doc = frappe.get_doc("Journal Entry",self.j)
			frappe.msgprint(doc.name)
			self.j = ""
			self.save()
			if doc:
				frappe.msgprint("axxxxsd")

				doc.cancel()
				frappe.db.commit()

