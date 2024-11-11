# Mubashir Bashir


from __future__ import unicode_literals
import frappe
from frappe import _

from frappe.utils import today
from datetime import datetime, date, timedelta

def execute(filters=None):
	columns, data = [], []
	
	
	user = frappe.session.user

	if filters.get("report_type") == "Absentees":
		columns = get_absentess_columns()
		data = get_absentees(filters, user)
	
	if filters.get("report_type") == "Late Arrival":
		columns = get_late_arrival_columns()
		data = get_late_arrival(filters, user)

	if filters.get("report_type") == "Early Leavers":
		columns = get_early_leavers_columns()
		data = get_early_leavers(filters, user)

	if filters.get("report_type") == "Check In/Out Missing":
		columns = get_check_in_out_columns()
		data = get_check_in_out(filters, user)

	if filters.get("report_type") == "Pending Attendance Requests":
		columns = get_pending_attendance_requests_columns()
		data = get_pending_attendance_requests(filters, user)
	
	if filters.get("report_type") == "Pending Leaves":
		columns = get_pending_leaves_columns()
		data = get_pending_leaves(filters, user)
	
	if filters.get("report_type") == "Approved Leaves":
		columns = get_approved_leaves_columns()
		data = get_approved_leaves(filters, user)

# Not Applicable	
	# if filters.get("report_type") == "Pending Comp Off Requests":
	# 	columns = get_pending_comp_off_requests_columns()
	# 	data = get_pending_comp_off_requests(filters, user)

	# if filters.get("report_type") == "Approved Comp Off":
	# 	columns = get_approved_comp_off_columns()
	# 	data = get_approved_comp_off(filters, user)
		
	
	return columns, data


# Absentees @@@
def get_absentess_columns():
	return [
		_("Employee ID") + ":Link/Employee:120",
		_("Employee name") + ":Data:120",
		_("Gender") + ":Data:120",
		_("Designation") + ":Data:120",
		_("Department") + ":Data:120",
		_("Region") + ":Data:120",
		_("Status") + ":Data:120",
		_("Attendance Date") + ":Date:120",
	]
# 

def get_absentees(filters, user):
    # Step 1: Generate conditions based on the filter input
    conditions = ""
    if filters.get("company"):
        conditions += " and emp.company = %(company)s"
    if filters.get("employee"):
        conditions += " AND emp.name = %(employee)s"
    if filters.get("branch"):
        conditions += " AND emp.branch = %(branch)s"
    if filters.get("department"):
        conditions += " AND emp.department = %(department)s"

    # Step 2: Get date range from from_date to to_date (as datetime.date objects)
    date_range = []
    start_date = datetime.strptime(filters.get("from_date"), "%Y-%m-%d").date()
    end_date = datetime.strptime(filters.get("to_date"), "%Y-%m-%d").date()
    current_date = start_date
    while current_date <= end_date:
        date_range.append(current_date)
        current_date += timedelta(days=1)

    # Step 3: Fetch holiday dates for employees in the filter
    holiday_query = """
        SELECT holiday_date FROM `tabHoliday`
        WHERE parent in (SELECT holiday_list FROM `tabEmployee` emp WHERE emp.status = 'Active' {condition})
        AND holiday_date BETWEEN %(from_date)s AND %(to_date)s
    """.format(condition=conditions)
    
    holiday_dates = frappe.db.sql(holiday_query, filters)
    # Convert holiday dates to a set of datetime.date objects for easy comparison
    holiday_list = {h[0] if isinstance(h[0], date) else datetime.strptime(h[0], "%Y-%m-%d").date() for h in holiday_dates}


    # Debugging statement to confirm holiday_list dates
    # frappe.msgprint(f"Holiday List Dates (Processed): {frappe.as_json(list(holiday_list))}")

    # Step 4: Fetch all active employees based on filters
    if "HR Manager" in frappe.get_roles(user):
        employee_query = """SELECT emp.name, emp.employee_name, emp.gender, emp.designation, emp.department, emp.custom_region
                            FROM `tabEmployee` emp
                            WHERE emp.status = 'Active' {condition}""".format(condition=conditions)
        employee_list = frappe.db.sql(employee_query, filters, as_dict=True)
    else:
        employee_query = """SELECT emp.name, emp.employee_name, emp.gender, emp.designation, emp.department, emp.custom_region
                            FROM `tabEmployee` emp, `tabUser Permission` per
                            WHERE emp.status = 'Active' 
                            AND per.allow = 'Employee' 
                            AND per.user = '{id}' 
                            AND emp.name = per.for_value {condition}""".format(id=user, condition=conditions)
        employee_list = frappe.db.sql(employee_query, filters, as_dict=True)

    # Step 5: Check attendance records and identify absences
    absent_result = []
    for employee in employee_list:
        for day in date_range:
            # Skip holiday dates
            if day in holiday_list:
                continue

            # Check if an attendance record exists for this employee on this day
            attendance_exists = frappe.db.exists("Attendance", {
                "employee": employee["name"],
                "attendance_date": day.strftime("%Y-%m-%d"),
                "docstatus": 1
            })

            # If no attendance record exists, mark as absent
            if not attendance_exists:
                absent_result.append({
                    "employee": employee["name"],
                    "employee_name": employee["employee_name"],
                    "gender": employee["gender"],
                    "designation": employee["designation"],
                    "department": employee["department"],
                    "custom_region": employee["custom_region"],
                    "status": "Absent",
                    "attendance_date": day.strftime("%Y-%m-%d")  # Format date as string
                })

    # Debugging statement to confirm final absent_result
    # frappe.msgprint(f"Absent Result: {frappe.as_json(absent_result)}")
                
    return absent_result


# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


 
# Late Arrivals @@@
def get_late_arrival_columns():
	return [
		_("Employee ID") + ":Link/Employee:120",
		_("Employee name") + ":Data:120",
		_("Designation") + ":Data:120",
		_("Department") + ":Data:120",
		_("Branch") + ":Data:120",
		_("Shift Check In") + ":Data:150",
		_("Check In") + ":Data:120",
		_("Late Entry Time") + ":Data:150",
		_("Check In Status") + ":Data:150",
		_("Status") + ":Data:120",
		_("Attendance Date") + ":Date:120",

	]
# 
def get_late_arrival(filters, user):
	
	conditions = ""
	if filters.get("company"):
		conditions += " and att.company = %(company)s"
	if filters.get("employee"):
		conditions += " AND att.employee = %(employee)s"
	if filters.get("branch"):
		conditions += " AND att.custom_branch = %(branch)s"
	if filters.get("department"):
		conditions += " AND att.department = %(department)s"
	if filters.get("from_date") and filters.get("to_date"):
		conditions += " and att.attendance_date BETWEEN %(from_date)s AND %(to_date)s"
	
	if "HR Manager" in frappe.get_roles(user):
		late_query = """ SELECT att.employee, att.employee_name, att.custom_designation, att.department, att.custom_branch, cast(att.custom_start_time as time) as from_time,  
				cast(att.in_time as time) as check_in_time, TIMEDIFF(cast(att.in_time as time), cast(att.custom_start_time as time)) AS late_entry_time, CASE WHEN att.late_entry = 1 THEN 'Late' WHEN att.late_entry = 0 THEN 'on Time' END AS late_status, att.status, att.attendance_date    
				FROM `tabAttendance` att
				WHERE  att.docstatus = 1 and late_entry = 1 and att.status = "Present" {condition} order by  att.late_entry desc  """.format(condition = conditions)
		# Database
		late_arrival_result = frappe.db.sql(late_query, filters)
	else:
		late_query = """ SELECT att.employee, att.employee_name, att.custom_designation, att.department, att.custom_branch, cast(att.custom_start_time as time) as from_time,  
				cast(att.in_time as time) as check_in_time, TIMEDIFF(cast(att.in_time as time), cast(att.custom_start_time as time)) AS late_entry_time, CASE WHEN att.late_entry = 1 THEN 'Late' WHEN att.late_entry = 0 THEN 'on Time' END AS late_status, att.status, att.attendance_date      
				FROM `tabAttendance` att INNER JOIN `tabUser Permission` per ON (att.employee=per.for_value)
				WHERE  att.docstatus = 1 and late_entry = 1 and att.status = "Present" and per.user='{id}' and per.allow='Employee'   {condition} 
				group by att.employee
				order by  att.late_entry desc  """.format(id=user,condition = conditions)
        # Database
		late_arrival_result = frappe.db.sql(late_query, filters)
	
	
	return late_arrival_result

# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
 
 
# Early Leavers @@@

def get_early_leavers_columns():
	return [
		_("Employee ID") + ":Link/Employee:120",
		_("Employee name") + ":Data:120",
		_("Designation") + ":Data:120",
		_("Department") + ":Data:120",
		_("Branch") + ":Data:120",
		_("Shift Check Out") + ":Data:150",
		_("Check Out") + ":Data:120",
		_("Early Left Time") + ":Data:150",
		_("Check Out Status") + ":Data:150",
		_("Status") + ":Data:120",
		_("Attendance Date") + ":Date:120",

	]
# 
def get_early_leavers(filters, user):
	
	conditions = ""
	if filters.get("company"):
		conditions += " and att.company = %(company)s"
	if filters.get("employee"):
		conditions += " AND att.employee = %(employee)s"
	if filters.get("branch"):
		conditions += " AND att.custom_branch = %(branch)s"
	if filters.get("department"):
		conditions += " AND att.department = %(department)s"
	if filters.get("from_date") and filters.get("to_date"):
		conditions += " and att.attendance_date BETWEEN %(from_date)s AND %(to_date)s"
	
	if "HR Manager" in frappe.get_roles(user):
		late_query = """ SELECT att.employee, att.employee_name, att.custom_designation, att.department, att.custom_branch, cast(att.custom_end_time as time) as from_time,  
				cast(att.out_time as time) as check_out_time, TIMEDIFF(cast(att.custom_end_time as time), cast(att.out_time as time)) AS early_left_time, CASE WHEN att.early_exit = 1 THEN 'Early Exit' WHEN att.early_exit = 0 THEN 'on Time' END AS early_exit_status, att.status, att.attendance_date     
				FROM `tabAttendance` att
				WHERE  att.docstatus = 1 and early_exit = 1 and att.status = "Present" {condition} order by  att.early_exit desc  """.format(condition = conditions)
		# Database
		late_arrival_result = frappe.db.sql(late_query, filters)
	else:
		late_query = """ SELECT att.employee, att.employee_name, att.custom_designation, att.department, att.custom_branch, cast(att.custom_end_time as time) as from_time,  
				cast(att.out_time as time) as check_out_time, TIMEDIFF(cast(att.custom_end_time as time), cast(att.out_time as time)) AS early_left_time, CASE WHEN att.early_exit = 1 THEN 'Early Exit' WHEN att.early_exit = 0 THEN 'on Time' END AS early_exit_status, att.status, att.attendance_date      
				FROM `tabAttendance` att INNER JOIN `tabUser Permission` per ON (att.employee=per.for_value)
				WHERE  att.docstatus = 1 and early_exit = 1 and att.status = "Present" and per.user='{id}' and per.allow='Employee'   {condition} 
				group by att.employee
				order by  att.early_exit desc  """.format(id=user,condition = conditions)
        # Database
		late_arrival_result = frappe.db.sql(late_query, filters)
	
	return late_arrival_result

# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
 
# Early Leavers @@@

def get_check_in_out_columns():
	return [
		_("Employee ID") + ":Link/Employee:120",
		_("Employee name") + ":Data:150",
		_("Designation") + ":Data:150",
		_("Department") + ":Data:150",
		_("Branch") + ":Data:120",
		_("Date") + ":Data:120",
		_("Check In/Out") + ":Data:150"

	]

def get_check_in_out(filters, user):

	conditions = ""
	if filters.get("company"):
		conditions += " and att.company = %(company)s"
	if filters.get("employee"):
		conditions += " AND att.employee = %(employee)s"
	if filters.get("branch"):
		conditions += " AND att.custom_branch = %(branch)s"
	if filters.get("department"):
		conditions += " AND att.department = %(department)s"
	if filters.get("from_date") and filters.get("to_date"):
		conditions += " and att.attendance_date BETWEEN %(from_date)s AND %(to_date)s"
        
	if "HR Manager" in frappe.get_roles(user):
		query=""" SELECT  att.employee, att.employee_name, att.custom_designation, att.department, att.custom_branch, att.attendance_date,
            (case
				when  att.in_time is null and att.out_time is null then 'Check In/Out Missed'
				when att.in_time is null then 'Check In Missed'
				when att.out_time is null then 'Check Out Missed'
				else 'On Time' 
			end) as in_out
            FROM `tabAttendance` att
            WHERE docstatus=1 and status='Present' and (in_time is null or out_time is null) {condition}
            order by employee_name
             """.format(condition = conditions)
		result = frappe.db.sql(query, filters, as_dict=0)
	else:
		query=""" SELECT  att.employee, att.employee_name, att.custom_designation, att.department, att.custom_branch, att.attendance_date,
            (case
				when  att.in_time is null and att.out_time is null then 'Check In/Out Missed'
				when att.in_time is null then 'Check In Missed'
				when att.out_time is null then 'Check Out Missed'
				else 'On Time' 
			end) as in_out
            FROM `tabAttendance` att,   `tabUser Permission` per
            WHERE att.docstatus=1 and att.status='Present' and (att.in_time is null or att.out_time is null)
            and att.employee=per.for_value and per.user='{id}' and per.allow='Employee' 
            {condition}
			group by att.employee
            order by att.employee_name  """.format(id=user, condition = conditions)
		result = frappe.db.sql(query, filters, as_dict=0)
	return result

# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


# ---Pending Attendance Requests @@@
def get_pending_attendance_requests_columns():
	return [
		_("Employee ID") + ":Link/Employee:120",
		_("Employee name") + ":Data:120",
		_("Department") + ":Data:120",
		_("Designation") + ":Data:120",
		_("Branch") + ":Data:120",
		_("From Time") + ":Data:120",
		_("To Time") + ":Data:120",
		_("Attendance Date") + ":Data:120",
		_("Feedback") + ":Data:220",
		_("Status") + ":Data:220",
	]

def get_pending_attendance_requests(filters, user):
    
	conditions = ""
	if filters.get("company"):
		conditions += " and lr.company = %(company)s"
	if filters.get("employee"):
		conditions += " AND lr.employee = %(employee)s"
	if filters.get("branch"):
		conditions += " AND lr.custom_branch = %(branch)s"
	if filters.get("department"):
		conditions += " AND lr.department = %(department)s"
	if filters.get("from_date") and filters.get("to_date"):
		conditions += " and lr.from_date BETWEEN %(from_date)s AND %(to_date)s"

	if "HR Manager" in frappe.get_roles(user):
		query =""" 
                SELECT lr.employee, lr.employee_name, lr.department, lr.designation, lr.custom_branch, cast(lr.custom_from as time) as from_time, cast(lr.custom_to as time) as to_time, lr.from_date, lr.reason, lr.custom_approval_status
                FROM `tabAttendance Request` lr
                WHERE lr.docstatus = 0 {condition}
                order by to_date desc  """.format(condition = conditions)
        # Database
		result = frappe.db.sql(query, filters)
	else:
		query =""" 
    			SELECT lr.employee, lr.employee_name, lr.department, lr.designation, lr.custom_branch, cast(lr.custom_from as time) as from_time, cast(lr.custom_to as time) as to_time, lr.from_date, lr.reason, lr.custom_approval_status
        		FROM `tabAttendance Request` lr, `tabUser Permission` per
        		WHERE lr.docstatus = 0 and lr.employee = per.for_value  and per.user='{id}' and per.allow='Employee'  {condition}
				group by lr.employee
        		order by to_date desc  """.format(id=user, condition = conditions)
		# Database
		result = frappe.db.sql(query, filters)
	return result

# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


# Pending Leaves @@@
def get_pending_leaves_columns():
	return [
		_("Employee ID") + ":Link/Employee:120",
		_("Employee name") + ":Data:120",
		_("Leave Type") + ":Data:120",
		_("Department") + ":Data:120",
		_("Branch") + ":Data:120",
		_("Designation") + ":Data:120",
		_("From Date") + ":Data:120",
		_("To Date") + ":Data:120",
		_("Total Leave Days") + ":Data:120",
		_("Status") + ":Data:120",
	]
# 
def get_pending_leaves(filters, user):

	conditions = get_leave_condition(filters)
	if "HR Manager" in frappe.get_roles(user):
		query =""" 
                SELECT la.employee, la.employee_name, la.leave_type, la.department, la.custom_branch, la.custom_designation, la.from_date, la.to_date, la.total_leave_days, la.status 
                FROM `tabLeave Application` la WHERE  la.docstatus = 0 and la.status='Open' {condition}
                order by la.total_leave_days desc  """.format(condition = conditions)
    	# Database
		result = frappe.db.sql(query, filters)
	else:
		query =""" 
            SELECT la.employee, la.employee_name, la.leave_type, la.department, la.custom_branch, la.custom_designation, la.from_date, la.to_date, la.total_leave_days, la.status 
            FROM `tabLeave Application` la, `tabUser Permission` per  
            WHERE  la.docstatus = 0 and la.status='Open' and la.employee = per.for_value  and per.user='{id}' and per.allow='Employee' {condition}
            group by la.employee
            order by la.total_leave_days desc  """.format(id=user,condition = conditions)
		# Database
		result = frappe.db.sql(query, filters)
	return result
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

# ---Approved Leaves @@@
def get_approved_leaves_columns():
	return [
		_("Employee ID") + ":Link/Employee:120",
		_("Employee name") + ":Data:120",
		_("Department") + ":Data:120",
		_("Branch") + ":Data:120",
		_("Designation") + ":Data:120",
		_("From Date") + ":Data:120",
		_("To Date") + ":Data:120",
		_("Total Leave Days") + ":Data:120",
		_("Leave Type") + ":Data:120",
	]

def get_approved_leaves(filters, user):
	conditions = get_leave_condition(filters)
	if "HR Manager" in frappe.get_roles(user):
		query =""" 
				SELECT la.employee, la.employee_name, la.department, la.custom_branch, la.custom_designation, la.from_date, la.to_date, la.total_leave_days, la.leave_type
				FROM `tabLeave Application` la
				WHERE la.docstatus= 1 and la.status='Approved' {condition}  
				order by la.posting_date desc  """.format(condition = conditions)
		# Database
		result = frappe.db.sql(query, filters)
	else:
		query =""" 
                SELECT la.employee, la.employee_name, la.department, la.custom_branch, la.custom_designation, la.from_date,la.to_date, la.total_leave_days, la.leave_type
                FROM `tabLeave Application` la, `tabUser Permission` per
                WHERE la.docstatus= 1 and la.status='Approved' 
                and la.employee=per.for_value and per.user='{id}' and per.allow='Employee'
                {condition}
				group by la.employee
                order by la.posting_date desc  """.format(id=user, condition = conditions)
		result = frappe.db.sql(query, filters)
	return result
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


###########################################
# Filter data condtions
def get_attendance_condition(filters):
    conditions = ""
    if filters.get("company"):
        conditions += " and att.company = %(company)s"
    if filters.get("employee"):
        conditions += " AND att.employee = %(employee)s"
    if filters.get("branch"):
        conditions += " AND att.custom_branch = %(branch)s"
    if filters.get("department"):
        conditions += " AND att.department = %(department)s"
    if filters.get("from_date") and filters.get("to_date"):
        conditions += " and att.attendance_date BETWEEN %(from_date)s AND %(to_date)s"
    
    return conditions  

# Filter data conditions
def get_leave_condition(filters):
    conditions = ""
    if filters.get("company"):
        conditions += " and la.company = %(company)s"
    if filters.get("employee"):
        conditions += " AND la.employee = %(employee)s"
    if filters.get("branch"):
        conditions += " AND la.custom_branch = %(branch)s"
    if filters.get("department"):
        conditions += " AND la.department = %(department)s"
    if filters.get("from_date") and filters.get("to_date"):
        conditions += " and la.from_date BETWEEN %(from_date)s AND %(to_date)s"
    
    return conditions  

#---Processing-Ending---##############################################################




# # ---Pending Comp Off Requests @@@
# def get_pending_comp_off_requests_columns():
# 	return [
# 		_("Employee Code") + ":Data:120",
# 		_("Employee name") + ":Data:120",
# 		_("Designation") + ":Data:120",
# 		_("Department") + ":Data:120",
# 		_("From Time") + ":Data:120",
# 		_("To Time") + ":Data:120",
# 		_("Applying Hours") + ":Data:120",
# 		_("Total Comp Off Balance") + ":Data:120",
# 		_("Feedback/Status") + ":Data:120",
# 	]
# # 
# def get_pending_comp_off_requests(filters, user):
# 	conditions = get_leave_condition(filters)
# 	if "HR Manager" in frappe.get_roles(user):
# 		query =""" 
#         		SELECT comp.employeecode, comp.employee_name, comp.designation, comp.department, comp.applying_date, 
#         		cast(comp.work_from as time) as work_from, cast(comp.work_to as time) as work_to, comp.applying_hours, comp.total_comp_off_balance, comp.status
#         		FROM `tabComp Off` comp
#         		WHERE comp.docstatus = 0 and comp.leave_type = 'Regular'
#     			{condition}  
#         		order by comp.posting_date desc  """.format(condition = conditions)
# 		# Database
# 		result = frappe.db.sql(query, filters)
# 	else:
# 		query =""" 
#             	SELECT comp.employeecode, comp.employee_name, comp.designation, comp.department, comp.applying_date, 
#             	cast(comp.work_from as time) as work_from, cast(comp.work_to as time) as work_to, comp.applying_hours, comp.total_comp_off_balance, comp.status
#             	FROM `tabComp Off` comp, `tabUser Permission` per
#             	WHERE comp.docstatus = 0 and comp.leave_type = 'Regular' 
#             	and comp.employee=per.for_value and per.user='{id}' and per.allow='Employee'
#             	{condition}
# 				group by comp.employee
#             	order by posting_date desc  """.format(id=user, condition = conditions)
# 		# Database
# 		result = frappe.db.sql(query, filters)
# 	return result
# # @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# # Approved Comp Off @@@
# def get_approved_comp_off_columns():
# 	return [
# 		_("Employee Code") + ":Data:120",
# 		_("Employee name") + ":Data:120",
# 		_("Designation") + ":/Department:120",
# 		_("Department") + ":Data:120",
# 		_("From Time") + ":Data:120",
# 		_("To Time") + ":Data:120",
# 		_("Applying Hours") + ":Data:120",
# 		_("Total Comp Off Balance") + ":Data:120",
# 		_("Feedback/Status") + ":Data:120",
# 	]

# def get_approved_comp_off(filters, user):
# 	conditions = get_leave_condition(filters)
# 	if "HR Manager" in frappe.get_roles(user):
# 		query =""" 
#         		SELECT employeecode, employee_name, designation, department, cast(work_from as time) as work_from, cast(work_to as time) as work_to, applying_hours,total_comp_off_balance, status 
#         		FROM `tabComp Off`
#         		WHERE docstatus=1 and leave_type = 'Regular' {condition}
#         		order by work_from, work_to  """.format(condition = conditions)
# 		# Database
# 		result = frappe.db.sql(query, filters)
# 	else:
# 		query =""" 
# 				SELECT comp.employeecode, comp.employee_name, comp.designation, comp.department, cast(comp.work_from as time) as work_from, cast(comp.work_to as time) as work_to, comp.applying_hours,comp.total_comp_off_balance, comp.status 
#             	FROM `tabComp Off` comp, `tabUser Permission` per
#             	WHERE comp.docstatus=1 and comp.leave_type = 'Regular' 
#             	and comp.employee=per.for_value and per.user='{id}' and per.allow='Employee' 
#             	{condition}
# 				group by comp.employee
#             	order by work_from, work_to  """.format(id=user, condition = conditions)
# 		# Database
# 		result = frappe.db.sql(query, filters)
# 	return result
# # @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
