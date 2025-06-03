from __future__ import unicode_literals
import frappe


@frappe.whitelist()
def emp_detail(emp):
	emp_name = frappe.db.get_value("Employee", emp, "employee_name")
	emp_designation = frappe.db.get_value("Employee", emp, "designation")
	emp_cnic = frappe.db.get_value("Employee", emp, "custom_cnic")
	emp_bank_name = frappe.db.get_value("Employee", emp, "bank_name")
	emp_ac_no = frappe.db.get_value("Employee", emp, "bank_ac_no")
	return emp_name, emp_designation, emp_cnic, emp_bank_name, emp_ac_no
