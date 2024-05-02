# Copyright (c) 2024, Nabeel Saleem and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class OvertimeClaimForm(Document):
	def autoname(self):
		from frappe.model.naming import make_autoname
		self.name = make_autoname(self.naming_series%{
			"employee_id": self.employee_id, 
			"month": self.month, 
			"year": self.year
			})