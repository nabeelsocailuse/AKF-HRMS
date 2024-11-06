# Mubashir Bashir

from __future__ import unicode_literals
import frappe
from frappe import _
def execute(filters=None):


	columns, data = [], []
	columns = get_employee_columns()
	data = get_employee_data(filters)
	return columns, data

def get_employee_columns():
	return [
		_("Name") + ":Data:120",
		_("Father") + ":Data:120",
		_("Department") + ":Link/Department:120",
		_("Designation") + ":Link/Designation:120",
		_("Contract Signed") + ":Data:120",
		_("Contract End") + ":Data:120",
		_("Branch") + ":Link/Branch:120",
		_("Reported to") + ":Link/Employee:120",
		_("Experience") + ":Data:120",
		_("DOB") + ":Data:120",
		_("Joining Date") + ":Data:120",
		_("Address") + ":Data:120",
		_("Primary Number") + ":Data:120",
		_("CNIC") + ":Data:120",
		_("Employment Type") + ":Data:120",
		_("Religion") + ":Data:120",
		_("Email") + ":Data:120",
		_("Personal Email") + ":Data:120",
		_("Working Hours") + ":Data:120",
		_("Bank Name") + ":Data:120",
		_("Bank Account") + ":Data:120",
		_("Confirmation Date") + ":Data:120",
		_("Grade") + ":Data:120",
		_("Last Promotion Date") + ":Date:120",
		_("Last Increment Date") + ":Date:120",
		_("Qualification") + ":Data:120",
		_("Gross Salary") + ":Currency:120",
		_("Pay by") + ":Data:120",
		_("Gender") + ":Data:120",
		_("Marital Status") + ":Data:120",
		_("From Shift") + ":Data:120",
		_("To Shift") + ":Data:120",
		_("Blood Group") + ":Data:120",
	]
# 


def get_employee_data(filters):
	
	conditions = get_conditions(filters)

	emp_record = """ 
		SELECT 
			e.employee_name, e.custom_father_name, e.department, e.designation,
			e.final_confirmation_date, e.contract_end_date, e.branch, e.reports_to,			
			(
				SELECT SUM(ewh.total_experience)
				FROM `tabEmployee External Work History` ewh
				WHERE ewh.parent = e.name
			) AS experience,
			e.date_of_birth, e.date_of_joining, e.current_address, e.cell_number,
			e.custom_cnic, e.employment_type, e.custom_religeon, e.prefered_email,
			e.personal_email, st.custom_total_working_hours, e.bank_name, e.bank_ac_no,
			e.final_confirmation_date, e.grade, ep.latest_promotion_date, lssa.latest_salary_structure,
			(
				SELECT 
					CASE 
						WHEN MAX(
							CASE 
								WHEN ed.level = 'Post Graduate' THEN 3
								WHEN ed.level = 'Graduate' THEN 2
								WHEN ed.level = 'Under Graduate' THEN 1
								ELSE 0 
							END
						) = 3 THEN 'Post Graduate'
						WHEN MAX(
							CASE 
								WHEN ed.level = 'Graduate' THEN 2
								ELSE 0 
							END
						) = 2 THEN 'Graduate'
						WHEN MAX(
							CASE 
								WHEN ed.level = 'Under Graduate' THEN 1
								ELSE 0 
							END
						) = 1 THEN 'Under Graduate'
						ELSE NULL
					END AS highest_education
				FROM `tabEmployee Education` ed
				WHERE ed.parent = e.name
			) AS qualification,
			(
				SELECT ssa.base 
				FROM `tabSalary Structure Assignment` ssa 
				WHERE ssa.employee = e.name 
				ORDER BY ssa.from_date DESC 
				LIMIT 1
			) AS base, 
			e.salary_mode, e.gender, e.marital_status, st.start_time, st.end_time,
			e.blood_group

		FROM `tabEmployee` e
		LEFT JOIN `tabShift Type` st ON e.default_shift = st.name
		LEFT JOIN (
				SELECT employee, MAX(promotion_date) AS latest_promotion_date
				FROM `tabEmployee Promotion`
				GROUP BY employee	
			  ) ep ON e.name = ep.employee
		LEFT JOIN (
				SELECT employee, MAX(from_date) AS latest_salary_structure
				FROM `tabSalary Structure Assignment`
				GROUP BY employee	
			  ) lssa ON e.name = lssa.employee
		WHERE {condition}
		""".format(condition = conditions)		
	
	

	data = frappe.db.sql(emp_record, filters)

	# frappe.msgprint(frappe.as_json(data))
	
	return data


def get_conditions(filters):
	conditions = ""
	if filters.get("company"):
		conditions += " e.company = %(company)s"
	if filters.get("employee"):
		conditions += " and e.employee = %(employee)s"
	if filters.get("department"):
		conditions += " and e.department = %(department)s"
	if filters.get("region"):
		conditions += " and e.custom_region = %(region)s"
	if filters.get("department"):
		conditions += " and e.department = %(department)s"
	if filters.get("branch"):
		conditions += " and e.branch = %(branch)s"
	if filters.get("status"):
		conditions += " and e.status = %(status)s"
	# if filters.get("from_date") and filters.get("to_date"):
	# 	conditions += " and att.attendance_date between %(from_date)s and %(to_date)s"
	
	return conditions
