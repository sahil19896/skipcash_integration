import frappe
from frappe import _

# document method update
def raise_no_permission_to(self, perm_type):
    """Raise `frappe.PermissionError`."""
    if(self.doctype not in ["Payment Entry"]):
        frappe.flags.error_message = _('Insufficient Permission for {0}, {1}').format(self.doctype, self.owner)
        raise frappe.PermissionError
