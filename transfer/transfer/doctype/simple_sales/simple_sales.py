# Copyright (c) 2025, awad mohamed & atta almanan and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from transfer.transfer.api import get_main_account
# ! Forgin Account Sales , Buy


# def add_custom_link(source_doctype, source_name, target_doctype, target_name):
#     # Update a field in the source document to track the link
#     source_doc = frappe.get_doc(source_doctype, source_name)
#     source_doc.append(
#         "linked_documents", {"doctype": target_doctype, "docname": target_name}
#     )
#     source_doc.save()


class SimpleSales(Document):
    def on_cancel(self):
        if self.si:
            # Cancel the associated Sales Invoice

            # Fetch associated Payment Entries from the Payment Entry Reference table
            try:
                payment_entries = frappe.get_all(
                    "Payment Entry Reference",
                    filters={
                        "reference_doctype": "Sales Invoice",
                        "reference_name": self.si,
                    },
                    fields=["parent"],
                )

                # Loop through all Payment Entries and cancel them
                for pe in payment_entries:
                    payment_entry = frappe.get_doc("Payment Entry", pe.parent)
                    payment_entry.cancel()
                    print(f" AAAAAAAAAAAA {payment_entry.name}")
                sales_invoice = frappe.get_doc("Sales Invoice", self.si)
                sales_invoice.cancel()
            except Exception as e:
                frappe.throw("cant cancel resoens", e)

        else:
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
                    frappe.throw(
                        _("ERROR CODE : (Simple Sales): Does not exitest 00011")
                    )
        frappe.db.set_value("Simple Sales", self.name, "status", "Cancelled")

    def on_submit(doc, method="submit"):
        # Ensure payment mode is always "Cash"
        try:
            discount = 0
            total_amount = doc.amount

            if doc.discount:
                total_amount = doc.amount - doc.discount
                discount = doc.discount
            if doc.payment_mode != "Cash":
                doc.payment_mode = "Cash"
            if doc.to == "Customer":
                sales_invoice = doc.createSalesInvoice(discount, total_amount)
                doc.status = "Paid"

                # print(f"asdkjas kdlkjaskdj {doc.si}")
            else:
                sales_invoice = doc.createSalesInvoice(
                    discount, total_amount, customer=doc.to_company
                )
                doc.si = sales_invoice.name
                doc.status = "Unpaid"
            doc.save()
            doc.submit()
            frappe.db.commit()

            if doc.to == "Customer":
                # ! payment should be made only for regular Customer
                payment_entry = doc.createPayment(total_amount, sales_invoice)

                frappe.msgprint(
                    _(
                        f"Sales Invoice {sales_invoice.name} and Payment Entry {payment_entry.name} created."
                    )
                )
        except Exception as e:
            # Handle the insufficient stock error
            frappe.msgprint(f"Error: {e}")
            frappe.throw(f"Error: {e}")

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
def get_payment_status(sales_invoice_name):
    sales_invoice = frappe.get_doc("Sales Invoice", sales_invoice_name)

    # Check if the invoice is cancelled
    if sales_invoice.docstatus == 2:
        return "Cancelled"

    total_paid = sales_invoice.outstanding_amount
    total_due = sales_invoice.grand_total

    # Determine payment status
    if total_paid == 0:
        return "Paid"
    elif total_paid < total_due:
        return "Partially Paid"
    elif total_paid == total_due:
        return "Unpaid"
    else:
        return "Overpaid"


@frappe.whitelist()
def get_related_documents(simple_sales_name):
    # Fetch Payment Entries based on the `reference_no` field

    payment_entries = frappe.get_all(
        "Payment Entry",
        filters={"reference_no": simple_sales_name},
        fields=["name"],
    )

    if not payment_entries:
        return {"payment_entries": [], "sales_invoice": None}

    # Fetch the Sales Invoice linked to the first Payment Entry
    payment_entry_name = payment_entries[0].get("name")
    references = frappe.get_all(
        "Payment Entry Reference",
        filters={"parent": payment_entry_name, "reference_doctype": "Sales Invoice"},
        fields=["reference_name"],
    )

    sales_invoice = references[0]["reference_name"] if references else None

    return {"payment_entries": payment_entries, "sales_invoice": sales_invoice}


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


def update_state_on_payment(doc, method):
    """
    Hook to update the state of a Simple Sales document based on payment status.
    """
    # Get the related Simple Sales document
    simple_sales = frappe.get_all(
        "Simple Sales",
        filters={"si": doc.references[0].reference_name},
        fields=["name"],
    )
    frappe.db.set_value("Simple Sales", simple_sales[0].name, "status", "Paid")


def on_payment_submit(doc, method):
    """
    Automatically mark related document as paid when a Payment Entry is submitted.
    """
    print("on_payment_submit on_payment_submi ton_payment_s ubmiton_payment_submit")
    # Check if the Payment Entry is linked to a Sales Invoice
    if doc.references:
        for reference in doc.references:
            if reference.reference_doctype == "Sales Invoice":
                sales_invoice_name = reference.reference_name

                # Fetch the related custom DocType using a link field or custom logic
                simple_sales = frappe.get_all(
                    "Simple Sales",
                    filters={
                        "si": sales_invoice_name
                    },  # Assuming `si` links to Sales Invoice
                    fields=["name"],
                )

                if simple_sales:
                    # Update the payment status in the Simple Sales document
                    simple_sales_name = simple_sales[0]["name"]
                    frappe.db.set_value(
                        "Simple Sales", simple_sales_name, "status", "Paid"
                    )
                    frappe.msgprint(f"Updated payment status for {simple_sales_name}")
