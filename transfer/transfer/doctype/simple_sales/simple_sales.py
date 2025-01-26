# Copyright (c) 2025, awad mohamed & atta almanan and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from transfer.transfer.api import get_main_account
# ! Forgin Account Sales , Buy


class SimpleSales(Document):
    def on_cancel(self):
        payment_entries = frappe.get_all(
            "Payment Entry", filters={"reference_no": self.name}, fields=["name"]
        )
        for pe in payment_entries:
            try:
                # Cancel the Payment Entry
                # frappe.db.set_value("Payment Entry", pe.name, "docstatus", 2)
                si = frappe.get_doc("Payment Entry", pe.name)
                si.cancel()
                # Get the Sales Invoice from the Payment Entry's references
                payment_entry = frappe.get_doc("Payment Entry", pe.name)
                for ref in payment_entry.references:
                    if ref.reference_doctype == "Sales Invoice":
                        # Cancel the Sales Invoice
                        # frappe.db.set_value(
                        #     "Sales Invoice", ref.reference_name, "docstatus", 2
                        # )
                        si = frappe.get_doc("Sales Invoice", ref.reference_name)
                        si.cancel()
                        break  # Exit the inner loop once the Sales Invoice is found
            except frappe.DoesNotExistError:
                frappe.throw(_("ERROR CODE : (Simple Sales): Does not exitest 00011"))

    def on_submit(doc, method="submit"):
        # Ensure payment mode is always "Cash"
        discount = 0
        total_amount = doc.amount
        company = doc.to_company
        if doc.discount:
            total_amount = doc.amount - doc.discount
            discount = doc.discount
        if doc.payment_mode != "Cash":
            doc.payment_mode = "Cash"
        if doc.to == "Customer":
            sales_invoice = doc.createSalesInvoice(discount, total_amount)
        else:
            sales_invoice = doc.createSalesInvoice(
                discount, total_amount, customer=doc.to_company
            )
        if doc.to == "Customer":
            # ! payment should be made only for regular Customer
            payment_entry = doc.createPayment(total_amount, sales_invoice)

            frappe.msgprint(
                _(
                    f"Sales Invoice {sales_invoice.name} and Payment Entry {payment_entry.name} created."
                )
            )

    def createPayment(doc, total_amount, sales_invoice):
        branch_account = get_main_account(doc.branch)

        # Create Payment Entry
        payment_entry = frappe.get_doc(
            {
                "doctype": "Payment Entry",
                "payment_type": "Receive",
                "mode_of_payment": "Cash",
                "paid_to_account_currency": "LYD",
                "paid_to": branch_account,
                "party_type": "Customer",
                "party": "زبون بنكك",  # Use Full Name as Party
                "party_name": "زبون بنكك",
                "paid_amount": total_amount,
                "received_amount": total_amount,
                "reference_no": doc.name,
                "reference_date": frappe.utils.nowdate(),
                "branch": doc.branch,
                "references": [
                    {
                        "reference_doctype": "Sales Invoice",
                        "reference_name": sales_invoice.name,
                        "allocated_amount": total_amount,
                        "total_amount": total_amount,
                    }
                ],
            }
        )
        payment_entry.insert()
        payment_entry.submit()
        return payment_entry

    def createSalesInvoice(doc, discount, total_amount, customer="زبون بنكك"):
        sales_invoice = frappe.get_doc(
            {
                "doctype": "Sales Invoice",
                "customer": customer,
                "contact_phone": doc.phone_number,
                "update_stock": 1,
                "disable_rounded_total": 1,
                "discount_amount": discount,
                "outstanding_amount": total_amount,
                "grand_total": total_amount,
                "branch": doc.branch,
                "items": [
                    {"item_code": doc.item, "qty": doc.quantity, "rate": doc.rate}
                ],
                "total": doc.amount,
                "due_date": doc.due_date,
                "remarks": doc.whatsapp_description,  # Add WhatsApp description
            }
        )
        sales_invoice.insert()
        sales_invoice.submit()
        return sales_invoice


# TODO create jounral entries that reflect on the simple sales if its buy or sale


@frappe.whitelist()
def get_related_documents(simple_sales_name):
    # Fetch Payment Entries based on the `reference_no` field
    payment_entries = frappe.get_all(
        "Payment Entry",
        filters={"reference_no": simple_sales_name},
        fields=["name"],
    )

    # Fetch Sales Invoices linked to the Payment Entries

    return {"payment_entries": payment_entries}


@frappe.whitelist()
def get_currency_selling_rate(base_currency, target_currency):
    rate = frappe.db.get_value(
        "Currency Exchange",
        {
            "from_currency": base_currency,
            "to_currency": target_currency,
        },
        "exchange_rate",
    )
    return rate
