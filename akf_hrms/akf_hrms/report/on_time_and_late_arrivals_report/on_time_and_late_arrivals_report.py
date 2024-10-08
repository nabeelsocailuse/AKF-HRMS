# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# Mubashir Bashir

from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
	columns, data = [], []
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_columns(filters):
	columns = [ _("Employee ID") + ":Link/Employee:180", _("Employee Name") + ":Data:200",
		_("Designation")+ ":Data:180",_("Department")+ ":Data:180",_("Branch")+ ":Data:150",_("Gender")+ ":Data:150", _("On Time")+ ":Int:150", _("Late Arrivals")+ ":Int:150" ]
	return columns

def get_data(filters):
    return_list = []
    conditions, filters = get_conditions(filters)
    emp_info = frappe.db.sql("""
        SELECT employee, employee_name, custom_designation, department,
        custom_branch, custom_gender, late_entry, attendance_date 
        FROM `tabAttendance`
        WHERE docstatus = 1 
        %s""" % conditions, filters)

    employee_data = {}  # Dictionary to store employee data with counts
    
    for emp in emp_info:
        if emp[0] not in employee_data: #
            employee_data[emp[0]] = {
                'employee_name': emp[1],
                'custom_designation': emp[2],
                'department': emp[3],
                'custom_branch': emp[4],
                'custom_gender': emp[5],
                'on_time_count': 0,
                'late_count': 0
            }
        
        if emp[6] == 0:
            employee_data[emp[0]]['on_time_count'] += 1   #the code updates the on_time_count and late_count values based on the attendance status (emp[8]) of the current record.
        if emp[6] == 1:
            employee_data[emp[0]]['late_count'] += 1
    
    for emp_id, emp_data in employee_data.items():
        return_list.append([
            emp_id,
            emp_data['employee_name'],
            emp_data['custom_designation'],
            emp_data['department'],
            emp_data['custom_branch'],
            emp_data['custom_gender'],
            emp_data['on_time_count'],
            emp_data['late_count']
        ])
    
    return return_list



    # for emp in emp_info:
    #     if emp.in_time_status == "On Time":
    #         on_time_count += 1
    #     elif emp.in_time_status == "Late":
    #         late_count += 1
    #     return_list.append([emp[0], emp[1], emp[2], emp[3], emp[4], emp[5], emp[6], emp[7], on_time_count, late_count])

    # return return_list


def get_conditions(filters):
	conditions = ""
	if filters.get("from_date") and filters.get("to_date"): conditions += " and attendance_date between %(from_date)s and %(to_date)s"
	if filters.get("company"): conditions += " and company = %(company)s"
	if filters.get("employee"): conditions += " and employee = %(employee)s"
	if filters.get("department"): conditions += " and department = %(department)s"

	return conditions, filters
