import frappe
from frappe import _
import requests
from erpnext.accounts.doctype.payment_request.payment_request import make_payment_entry, make_payment_request

@frappe.whitelist(allow_guest=True)
def get_payment_info(id):
    try:
        skipcash = frappe.get_doc("SKIPCash Settings", "SKIPCash Settings")
        url = "https://skipcashtest.azurewebsites.net/api/v1/payments/"+id
        headers = {'Authorization' : skipcash.client_id}
        skip = requests.get(url, headers=headers)
        if(skip.ok):
            data = skip.json()['resultObj']
            update_payment(data)
            return data
        else:
            return skip.reason
    except Exception as e:
        frappe.throw(e)

@frappe.whitelist(allow_guest=True)
def update_payment(data):
    try:
        docname = data['transactionId']
        payment_request = frappe.get_doc("Payment Request", docname)
        if not frappe.db.exists("Payment Entry", {"reference_no": data['visaId']}):
            entry = frappe.new_doc("Payment Entry")
            entry.payment_type = "Receive"
            entry.posting_date = frappe.utils.nowdate()
            entry.party_type = payment_request.party_type
            entry.party = payment_request.party
            entry.party_name = payment_request.party
            entry.paid_to = payment_request.payment_account
            entry.paid_from_account_currency = payment_request.currency
            entry.paid_from_to_currency = payment_request.currency

            entry.append("references", {
                "reference_doctype": payment_request.reference_doctype,
                "reference_name": payment_request.reference_name,
                "total_amount": payment_request.grand_total,
                "outstanding_amount": payment_request.grand_total,
                "allocated_amount": payment_request.grand_total,
                "due_date": frappe.utils.nowdate()
            })

            entry.paid_amount = payment_request.grand_total
            entry.reference_no = data['visaId']
            entry.reference_date = frappe.utils.nowdate()
            entry.received_amount = payment_request.grand_total
            entry.save(ignore_permissions=True)
            entry.submit()
        return True
    except Exception as e:
        frappe.throw(e)
