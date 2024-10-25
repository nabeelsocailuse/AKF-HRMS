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
	return [
		_("Employee") + ":Link/Employee:180", _("Employee Name") + "::180", _("Department") + ":Link/Department:150", _("Designation") + ":Link/Designation:150",   
		_("Branch") + ":Link/Branch:150", _("Employment Type") + ":Link/Employment Type:150", _("Grade") + "::150", _("Job Classification") + ":Link/Job Classification:150",
		_("Region") + ":data:150", _("Last Attendance Date") + ":date:180"
		]

def get_data(filters):
    return_list = []
    conditions, filters = get_conditions(filters)
    get_employee = frappe.db.sql("""select name, employee_name, department, designation, branch, employment_type, grade, custom_job_classification, custom_region 
                                    from `tabEmployee` 
                                    where custom_no_attendance=0 and status = 'Active' 
                                    and name not in (select distinct(employee) from `tabAttendance` where docstatus=1 %s)""" % conditions, filters, as_dict=1)
    for emp in get_employee:
        single_row = [
            emp.get("name"),
            emp.get("employee_name"),
            emp.get("department"),
            emp.get("designation"),
            emp.get("branch"),
            emp.get("employment_type"),
            emp.get("grade"),
            emp.get("custom_job_classification"),
            emp.get("custom_region")
        ]

        get_last_att = frappe.db.sql("""select distinct(attendance_date) 
                                        from `tabAttendance` 
                                        where docstatus=1 and employee=%s
                                        order by attendance_date desc """, (emp.get("name")))
        if get_last_att:
            single_row.append(frappe.utils.formatdate(get_last_att[0][0], "dd-MMM-yyyy"))
        else:
            single_row.append("")

        return_list.append(single_row)
    
    return return_list

def get_conditions(filters):
	conditions = ""
	if filters.get("company"):
		conditions += " and company = %(company)s"

	if filters.get("from_date") and filters.get("to_date"):
		conditions += " and attendance_date between %(from_date)s and %(to_date)s"

	return conditions,filters
