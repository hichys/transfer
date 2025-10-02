import frappe
from frappe.model.document import Document

class AlzawiaTransfer(Document):
    transfer_setting = frappe.get_cached_doc("Transfer Setting")
    def get_customer_accounts(self,cust_name):
        for row in self.transfer_setting.internal:
            if row.customer == cust_name:
                return row.cash_account, row.profit_account, True
        for row in self.transfer_setting.external:
            if row.customer == cust_name:
                return row.cash_account, None, False
        frappe.throw(f"Customer {cust_name} not found in Transfer Setting")

    def on_submit(self):
        company = frappe.defaults.get_global_default("company")
        if not company:
            frappe.throw("Default Company not set in ERPNext.")

        main_profit_account = self.get_customer_accounts(
            self.transfer_setting.main_branch
        )

        sender_cash, sender_profit, sender_internal = self.get_customer_accounts(
            self.from_customer
        )
        receiver_cash, receiver_profit, receiver_internal = self.get_customer_accounts(
            self.to_customer
        )

        if sender_internal and receiver_internal:
            accounts = self._handle_internal_to_internal(
                sender_cash, sender_profit, receiver_cash, receiver_profit
            )
        elif sender_internal and not receiver_internal:
            accounts = self._handle_internal_to_external(
                sender_cash, sender_profit, receiver_cash
            )
        elif not sender_internal and receiver_internal:
            accounts = self._handle_external_to_internal(
                sender_cash, receiver_cash, receiver_profit
            )
        else:  #TODO both external 
            accounts = self._handle_external_to_external(
                sender_cash, receiver_cash, main_profit_account
            )

        je = frappe.get_doc(
            {
                "doctype": "Journal Entry",
                "company": company,
                "voucher_type": "Journal Entry",
                "posting_date": frappe.utils.nowdate(),
                "accounts": accounts,
                "remark": self.whatsapp_desc,
            }
        )
        je.insert(ignore_permissions=True)
        je.submit()

        self.journal_entry = je.name
        self.save(ignore_permissions=True)

        frappe.msgprint(f"Journal Entry {je.name} created for this transfer")

    def _handle_internal_to_internal(
        self, sender_cash, sender_profit, receiver_cash, receiver_profit
    ):
        accounts = []
        accounts.append(
            {
                "account": sender_cash,
                "debit_in_account_currency": self.amount + self.total_profit,
                "credit_in_account_currency": 0,
            }
        )
        accounts.append(
            {
                "account": receiver_cash,
                "debit_in_account_currency": 0,
                "credit_in_account_currency": self.amount,
            }
        )
        if self.sender_profit:
            accounts.append(
                {
                    "account": sender_profit,
                    "debit_in_account_currency": 0,
                    "credit_in_account_currency": self.sender_profit,
                }
            )
        if self.receiver_profit:
            accounts.append(
                {
                    "account": receiver_profit,
                    "debit_in_account_currency": 0,
                    "credit_in_account_currency": self.receiver_profit,
                }
            )

        return accounts

    def _handle_internal_to_external(self, sender_cash, sender_profit, receiver_cash):
        accounts = []

        accounts.append(
            {
                "account": sender_cash,
                "debit_in_account_currency": self.amount + self.total_profit,
                "credit_in_account_currency": 0,
            }
        )
        accounts.append(
            {
                "account": receiver_cash,
                "debit_in_account_currency": 0,
                "credit_in_account_currency": self.amount + self.receiver_profit,
            }
        )

        accounts.append(
                {
                    "account": sender_profit,
                    "debit_in_account_currency": 0,
                    "credit_in_account_currency": (self.sender_profit or 0),
                }
            )

        return accounts

    def _handle_external_to_internal(self, sender_cash, receiver_cash, receiver_profit):
        accounts = []

        accounts.append(
            {
                "account": sender_cash,
                "debit_in_account_currency": self.amount + (self.receiver_profit or 0),
                "credit_in_account_currency": 0,
            }
        )
        accounts.append(
            {
                "account": receiver_cash,
                "debit_in_account_currency": 0,
                "credit_in_account_currency": self.amount,
            }
        )

        if self.receiver_profit:
            accounts.append(
                {
                    "account": receiver_profit,
                    "debit_in_account_currency": 0,
                    "credit_in_account_currency": self.receiver_profit,
                }
            )

        return accounts

    def _handle_external_to_external(self, sender_cash, receiver_cash,main_profit_account):
        accounts = []

        accounts.append(
            {
                "account": sender_cash,
                "debit_in_account_currency": self.amount + self.receiver_profit + self.alzawia_profit,
                "credit_in_account_currency": 0,
            }
        )
        accounts.append(
            {
                "account": receiver_cash,
                "debit_in_account_currency": 0,
                "credit_in_account_currency": (self.amount + self.receiver_profit),
            }
        )
        accounts.append(
            {
                "account": main_profit_account,
                "debit_in_account_currency": 0,
                "credit_in_account_currency": self.alzawia_profit,
            }
        )

        return accounts

    def on_cancel(self):
        if not self.journal_entry:
            frappe.msgprint("No Journal Entry to cancel.")
            return

        je_doc = frappe.get_doc("Journal Entry", self.journal_entry)

        # Same date → cancel JE
        if je_doc.posting_date == self.posting_date:
            if je_doc.docstatus == 1:  # submitted
                je_doc.cancel()
                frappe.msgprint(f"Journal Entry {je_doc.name} cancelled.")
        else:  # Reverse
            reversal_je = frappe.copy_doc(je_doc)
            reversal_je.name = None
            reversal_je.posting_date = frappe.utils.nowdate()
            reversal_je.voucher_type = "Journal Entry"
            reversal_je.remark = f"حوالة ملغية : {self.whatsapp_desc}"
            reversal_je.reversal_of = je_doc.name

            # Reverse debit/credit
            for d in reversal_je.accounts:
                d.debit_in_account_currency, d.credit_in_account_currency = (
                    d.credit_in_account_currency,
                    d.debit_in_account_currency,
                )

            reversal_je.insert(ignore_permissions=True)
            reversal_je.submit()

            frappe.msgprint(
                f"Reversal Journal Entry {reversal_je.name} created for cancelled transfer."
            )
