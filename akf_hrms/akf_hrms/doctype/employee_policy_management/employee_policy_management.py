# -*- coding: utf-8 -*-
# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class EmployeePolicyManagement(Document):
	def validate(self):
		# Sort Order must be unique
		emp_name = frappe.db.get_value("Employee Policy Management",{"name":["!=", self.name],"sort_order":self.sort_order}, "name")
		if emp_name:
			frappe.throw("Employee Policy Management '{0}' already have sort order {1}".format(emp_name, self.sort_order))