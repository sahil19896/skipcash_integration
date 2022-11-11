from frappe.model.document import Document
from skipcash_integration.api  import raise_no_permission_to
__version__ = '0.0.1'


Document.raise_no_permission_to = raise_no_permission_to
