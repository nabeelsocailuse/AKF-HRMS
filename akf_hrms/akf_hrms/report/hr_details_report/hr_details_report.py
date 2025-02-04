# Mubashir Bashir

import frappe
from frappe import _


def execute(filters=None):
	columns, data = [], []
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	column = []
	column.extend([
		_("Employee ID") + ":Link/Employee:150",
		_("Employee Name") + "::150",
		_("Status") + "::120",
		_("Relieving Date") + "::150",
		_("CNIC") + "::150",
		_("Department") + "::150",
		_("Designation") + "::150",
		_("Branch") + "::150",
		_("Salary Structure Assignment") + ":Link/Salary Structure Assignment:150",
		_("Holiday List") + "::150",
		_("Shift Assignment") + ":Link/Shift Assignment:150",
		_("Leave Allocation") + "::150",
	])
	return column

def get_data(filters):
	data = frappe.db.sql("""
		SELECT 
			e.name,
			e.employee_name, 
			e.status, 
			COALESCE(e.relieving_date, '-') AS relieving_date,
			COALESCE(e.custom_cnic, '-') AS custom_cnic,
			COALESCE(e.department, '-') AS department,
			COALESCE(e.designation, '-') AS designation,
			COALESCE(e.branch, '-') AS branch,
			
			COALESCE(
                (SELECT ssa.name 
                 FROM `tabSalary Structure Assignment` ssa 
                 WHERE ssa.employee = e.name AND ssa.docstatus = 1
                 ORDER BY ssa.from_date DESC 
                 LIMIT 1), 
                '-') AS latest_salary_structure_assignment,

			COALESCE(e.holiday_list, '-') AS holiday_list,

			COALESCE(
                (SELECT sa.name 
                 FROM `tabShift Assignment` sa 
                 WHERE sa.employee = e.name AND sa.status = 'Active' AND sa.docstatus = 1
                 ORDER BY sa.start_date DESC 
                 LIMIT 1), 
                '-') AS latest_shift_assignment, 		
					  	
			CASE 
				WHEN EXISTS (SELECT 1 FROM `tabLeave Allocation` la WHERE la.employee = e.name AND la.docstatus = 1) 
				THEN 'Yes' 
				ELSE 'No' 
			END AS leave_allocation_submitted
			
		FROM 
			`tabEmployee` e
		Where
			e.docstatus=0
			{0}
	 """.format(get_conditions(filters)), filters, as_dict=0)

	# frappe.msgprint(frappe.as_json(data))
	
	return data

def get_conditions(filters):
    conditions = ""
    conditions += " and e.company = %(company)s " if(filters.company) else ""
    conditions += " and e.branch = %(branch)s " if(filters.branch) else ""
    conditions += " and e.name = %(employee_id)s " if(filters.employee_id) else ""
    conditions += " and e.status = %(employee_status)s " if(filters.employee_status) else ""

    if filters.ssa:
        if filters.ssa == "Assigned":
            conditions += """ and (SELECT ssa.name 
                                   FROM `tabSalary Structure Assignment` ssa 
                                   WHERE ssa.employee = e.name AND ssa.docstatus = 1 
                                   ORDER BY ssa.from_date DESC 
                                   LIMIT 1) IS NOT NULL """
        elif filters.ssa == "Not Assigned":
            conditions += """ and (SELECT ssa.name 
                                   FROM `tabSalary Structure Assignment` ssa 
                                   WHERE ssa.employee = e.name AND ssa.docstatus = 1 
                                   ORDER BY ssa.from_date DESC 
                                   LIMIT 1) IS NULL """

    return conditions

	
