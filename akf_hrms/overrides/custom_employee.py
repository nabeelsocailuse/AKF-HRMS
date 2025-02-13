import frappe, re
from frappe.model.document import Document
from erpnext.setup.doctype.employee.employee import Employee

class XEmployee(Employee):
	def validate(self):
		super().validate()
		self.verify_identity_card_no()
	
	def verify_identity_card_no(self):
		details = get_country_details(self.custom_country)
		if (not match_regex(details.custom_id_regex, self.custom_cnic)):
			exception_msg('Please enter valid %s.'%details.custom_label)
        
@frappe.whitelist()
def get_country_details(country):
	return frappe.db.get_value('Country', {'name': country}, ["custom_label", "custom_id_mask", "custom_id_regex"], as_dict=1)

def match_regex(regex ,mystr):
	return re.match(regex, mystr)

def exception_msg(msg):
	frappe.throw(msg)

