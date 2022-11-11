# Copyright (c) 2022, M20Zero and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from six.moves.urllib.parse import urlencode
from frappe.utils import get_url, call_hook_method, cint, flt
from frappe.integrations.utils import make_get_request, make_post_request, create_request_log, create_payment_gateway
import requests, hmac, hashlib, base64, uuid, json
from six import string_types, text_type

class SKIPCashSettings(Document):
    supported_currencies = ["AED", "QR", "QAR"]
    currency_wise_minimum_charge_amount = {'AED': 0.50, 'QR': 0.50, "QAR": 0.50}

    def on_update(self):
        create_payment_gateway('SkipCash-Payment', settings='SKIPCash Settings', controller='SkipCash-Payment')
        call_hook_method('payment_gateway_enabled', gateway='SkipCash-Payment')

    def validate_transaction_currency(self, currency):
        if currency not in self.supported_currencies:
            frappe.throw(_("Please select another payment method. SkipCash does not support transactions in currency '{0}'").format(currency))

    def validate_minimum_transaction_amount(self, currency, amount):
        if currency in self.currency_wise_minimum_charge_amount:
            if flt(amount) < self.currency_wise_minimum_charge_amount.get(currency, 0.0):
                frappe.throw(_("For currency {0}, the minimum transaction amount should be {1}").format(currency, self.currency_wise_minimum_charge_amount.get(currency, 0.0)))

    def get_payment_url(self, **kwargs):
        try:
            args = {}
            data = urlencode(kwargs)
            for d in data.split("&"):
                value = d.split("=")
                args.update({value[0]: value[1]})

            email = frappe.db.get_value("Payment Request", {"name": args['order_id']}, "email_to")
            if not email:
                frappe.throw(_("Email Id in mandatory in Payment Request(<b>{0}</b>)").format(args['order_id']))
            guid = uuid.uuid4()
            pay_args = {"Uid": str(guid), "KeyId": self.key_id, "Amount": str("%.2f" % float(args['amount'])), "FirstName": args['payer_name'], "LastName": "-", "Email": email, "TransactionId": args['reference_docname']}

            signature = 'Uid={},KeyId={},Amount={},FirstName={},LastName={},Email={},TransactionId={}'.format(pay_args['Uid'], self.key_id, pay_args['Amount'], pay_args['FirstName'], pay_args['LastName'], pay_args['Email'], pay_args['TransactionId'])

            base = base64.b64encode(hmac.new(self.key_secret.encode(), signature.encode(), digestmod=hashlib.sha256).digest())
            headers = {'Authorization' : base}

            skip = requests.post(self.url, json=pay_args, headers=headers)
            if(skip.ok):
                data = json.loads(skip.text)
                self.create_request_logs(skip.text, "Host", "SkipCash", "Payment Request", pay_args['TransactionId'])
                url = data['resultObj']['payUrl']
                return url
            else:
                frappe.throw(_("{0}, {1}").format(skip.text, pay_args))
        except Exception as e:
            frappe.throw(frappe.get_traceback())


    def create_request_logs(self, data, integration_type, service_name, doctype, docname, name=None, error=None):
        if isinstance(data, string_types):
            data = json.loads(data)

        if isinstance(error, string_types):
            error = json.loads(error)

        integration_request = frappe.get_doc({
            "doctype": "Integration Request",
            "integration_type": integration_type,
            "integration_request_service": service_name,
            "reference_doctype": doctype,
            "reference_docname": docname,
            "error": json.dumps(error, default=self.json_handler),
            "data": json.dumps(data, default=self.json_handler)
        })

        if name:
            integration_request.flags._name = name

        integration_request.insert(ignore_permissions=True)
        frappe.db.commit()

    def json_handler(obj):
        if isinstance(obj, (datetime.date, datetime.timedelta, datetime.datetime)):
            return text_type(obj)
