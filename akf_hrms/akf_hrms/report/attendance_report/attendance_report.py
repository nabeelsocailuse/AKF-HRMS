



from __future__ import unicode_literals
from frappe import _
import frappe
import ast

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

	# if filters.get("report_type") == "Check In/Out Missing":
	# 	columns = get_check_in_out_columns()
	# 	data = get_check_in_out(filters, user)

	# if filters.get("report_type") == "Pending Attendance Requests":
	# 	columns = get_pending_attendance_requests_columns()
	# 	data = get_pending_attendance_requests(filters, user)
	
	# if filters.get("report_type") == "Pending Leaves":
	# 	columns = get_pending_leaves_columns()
	# 	data = get_pending_leaves(filters, user)
	
	# if filters.get("report_type") == "Approved Leaves":
	# 	columns = get_approved_leaves_columns()
	# 	data = get_approved_leaves(filters, user)
	
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
		_("Attendance ID") + ":Link/Attendance:120",
		_("Employee name") + ":Data:120",
		_("Gender") + ":Data:120",
		_("Designation") + ":Data:120",
		_("Department") + ":Data:120",
		_("Region") + ":Data:120",
		_("Feedback/Status") + ":Data:120",
	]
# 
def get_absentees(filters, user):
	conditions = get_attendance_condition(filters)
	
	if "HR Manager" in frappe.get_roles(user):
		# Query string
		absent_query = """ SELECT name, employee_name, custom_gender, custom_designation, department, custom_region, status FROM `tabAttendance` att
                	WHERE docstatus=1 and status='Absent'  {condition}  order by attendance_date desc""".format(condition = conditions)
		# Database
		absent_result = frappe.db.sql(absent_query, filters)
	else:
		absent_query = """SELECT att.name, att.employee_name, custom_gender, att.custom_designation, att.department, att.custom_region, att.status FROM `tabAttendance` att, `tabUser Permission` per 
        		WHERE att.docstatus=1 and att.status='Absent' and per.allow ='Employee' 
				and per.user = '{id}' and att.employee = per.for_value  {condition}
				group by att.employee
				order by att.attendance_date desc """.format(id =user , condition = conditions)
		absent_result = frappe.db.sql(absent_query, filters)
    
	return absent_result
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


 
# Late Arrivals @@@
def get_late_arrival_columns():
	return [
		_("Attendance ID") + ":Link/Attendance:120",
		_("Employee name") + ":Data:120",
		_("Designation") + ":Data:120",
		_("Department") + ":Data:120",
		_("Branch") + ":Data:120",
		_("Shift Check In") + ":Data:120",
		_("Check In") + ":Data:120",
		_("Total hours assigned") + ":Data:120",
		_("Check In Status") + ":Data:120",
		_("Feedback/Status") + ":Data:120",

	]
# 
def get_late_arrival(filters, user):
	
	conditions = ""
	if filters.get("department"):
		conditions += " and att.department = %(department)s"
	if filters.get("region"):
		conditions += " and att.custom_region = %(region)s"
	if filters.get("date"):
		conditions += " and att.attendance_date = %(date)s"
	
	if "HR Manager" in frappe.get_roles(user):
		late_query = """ SELECT att.name, att.employee_name, att.custom_designation, att.department, att.custom_branch, cast(att.custom_start_time as time) as from_time,  
				cast(att.in_time as time) as check_in_time, att.custom_total_working_hours, CASE WHEN att.late_entry = 1 THEN 'Late' WHEN att.late_entry = 0 THEN 'on Time' END AS late_status, att.status    
				FROM `tabAttendance` att
				WHERE  late_entry = 1 and att.status = "Present" {condition} order by  att.late_entry desc  """.format(condition = conditions)
		# Database
		late_arrival_result = frappe.db.sql(late_query, filters)
	else:
		late_query = """ SELECT att.name, att.employee_name, att.custom_designation, att.department, att.custom_branch, cast(att.custom_start_time as time) as from_time,  
				cast(att.in_time as time) as check_in_time, att.custom_total_working_hours, CASE WHEN att.late_entry = 1 THEN 'Late' WHEN att.late_entry = 0 THEN 'on Time' END AS late_status, att.status     
				FROM `tabAttendance` att INNER JOIN `tabUser Permission` per ON (att.employee=per.for_value)
				WHERE  late_entry = 1 and att.status = "Present" and per.user='{id}' and per.allow='Employee'   {condition} 
				group by att.employee
				order by  att.late_entry desc  """.format(id=user,condition = conditions)
        # Database
		late_arrival_result = frappe.db.sql(late_query, filters)
	
	return late_arrival_result

# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
 
# Early Leavers @@@

def get_early_leavers_columns():
	return [
		_("Attendance ID") + ":Link/Attendance:120",
		_("Employee name") + ":Data:120",
		_("Designation") + ":Data:120",
		_("Department") + ":Data:120",
		_("Branch") + ":Data:120",
		_("Shift Check In") + ":Data:120",
		_("Check In") + ":Data:120",
		_("Total hours assigned") + ":Data:120",
		_("Check In Status") + ":Data:120",
		_("Feedback/Status") + ":Data:120",

	]
# 
def get_early_leavers(filters, user):
	
	conditions = ""
	if filters.get("department"):
		conditions += " and att.department = %(department)s"
	if filters.get("region"):
		conditions += " and att.custom_region = %(region)s"
	if filters.get("date"):
		conditions += " and att.attendance_date = %(date)s"
	
	if "HR Manager" in frappe.get_roles(user):
		late_query = """ SELECT att.name, att.employee_name, att.custom_designation, att.department, att.custom_branch, cast(att.custom_start_time as time) as from_time,  
				cast(att.in_time as time) as check_in_time, att.custom_total_working_hours, CASE WHEN att.early_exit = 1 THEN 'Early Exit' WHEN att.early_exit = 0 THEN 'on Time' END AS early_exit_status, att.status    
				FROM `tabAttendance` att
				WHERE  early_exit = 1 and att.status = "Present" {condition} order by  att.early_exit desc  """.format(condition = conditions)
		# Database
		late_arrival_result = frappe.db.sql(late_query, filters)
	else:
		late_query = """ SELECT att.name, att.employee_name, att.custom_designation, att.department, att.custom_branch, cast(att.custom_start_time as time) as from_time,  
				cast(att.in_time as time) as check_in_time, att.custom_total_working_hours, CASE WHEN att.early_exit = 1 THEN 'Early Exit' WHEN att.early_exit = 0 THEN 'on Time' END AS early_exit_status, att.status     
				FROM `tabAttendance` att INNER JOIN `tabUser Permission` per ON (att.employee=per.for_value)
				WHERE  early_exit = 1 and att.status = "Present" and per.user='{id}' and per.allow='Employee'   {condition} 
				group by att.employee
				order by  att.early_exit desc  """.format(id=user,condition = conditions)
        # Database
		late_arrival_result = frappe.db.sql(late_query, filters)
	
	return late_arrival_result

# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
 
# Early Leavers @@@

def get_check_in_out_columns():
	return [
		_("Employee Code") + ":Data:120",
		_("Employee name") + ":Data:150",
		_("Designation") + ":/Department:150",
		_("Department") + ":Data:150",
		_("Region") + ":Data:120",
		_("Date") + ":Data:120",
		_("Check In/Out") + ":Data:150"

	]

def get_check_in_out(filters, user):

	conditions = ""
	if filters.get("department"):
		conditions += " and department = %(department)s"
	if filters.get("region"):
		conditions += " and region = %(region)s"
	if filters.get("date"):
		conditions += " and attendance_date = %(date)s"
        
	if "HR Manager" in frappe.get_roles(user):
		query=""" SELECT  employee_code, employee_name, designation, department, region, attendance_date,
            (case when check_in_time is not null and check_out_time is null and log_missed is not null then log_missed
		when  check_in_time is null and check_out_time is null then 'Both'
            else log_missed end) as in_out
            FROM `tabAttendance`
            WHERE docstatus=1 and status='Present' and check_in_time is not null and check_out_time is null and log_missed is not null {condition}
            order by employee_code
             """.format(condition = conditions)
		result = frappe.db.sql(query, filters, as_dict=0)
	else:
		query=""" SELECT  att.employee_code, att.employee_name, att.designation, att.department, att.region, att.attendance_date,
            (case when check_in_time is not null and check_out_time is null and log_missed is not null then log_missed
		 when  check_in_time is null and check_out_time is null then 'Both' 
            else log_missed end) as in_out
            FROM `tabAttendance` att,   `tabUser Permission` per
            WHERE att.docstatus=1 and att.status='Present' and att.check_in_time is not null and att.check_out_time is null and log_missed is not null
            and att.employee=per.for_value and per.user='{id}' and per.allow='Employee' 
            {condition}
			group by att.employee
            order by att.employee_code  """.format(id=user, condition = conditions)
		result = frappe.db.sql(query, filters, as_dict=0)
	return result


# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

# Pending Leaves @@@
def get_pending_leaves_columns():
	return [
		_("Employee Code") + ":Data:120",
		_("Employee name") + ":Data:120",
		_("Leave Type") + ":/Department:120",
		_("Department") + ":Data:120",
		_("Designation") + ":Data:120",
		_("From Date") + ":Data:120",
		_("To Date") + ":Data:120",
		_("Total Leave Days") + ":Data:120",
		_("Feedback/Status") + ":Data:120",
	]
# 
def get_pending_leaves(filters, user):

	conditions = get_leave_condition(filters)
	if "HR Manager" in frappe.get_roles(user):
		query =""" 
                SELECT employee_code, employee_name, leave_type, department, designation, from_date, to_date, total_leave_days, status 
                FROM `tabLeave Application` WHERE  docstatus = 0 and status='Open' {condition}
                order by total_leave_days desc  """.format(condition = conditions)
    	# Database
		result = frappe.db.sql(query, filters)
	else:
		query =""" 
            SELECT la.employee_code, la.employee_name, la.leave_type, la.department, la.designation, la.from_date, la.to_date, la.total_leave_days, la.status 
            FROM `tabLeave Application` la, `tabUser Permission` per 
            
            WHERE  la.docstatus = 0 and la.status='Open' and la.employee = per.for_value  and per.user='{id}' and per.allow='Employee' {condition}
            group by la.employee
            order by la.total_leave_days desc  """.format(id=user,condition = conditions)
		# Database
		result = frappe.db.sql(query, filters)
	return result
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

# ---Pending Attendance Requests @@@
def get_pending_attendance_requests_columns():
	return [
		_("Employee Code") + ":Data:120",
		_("Employee name") + ":Data:120",
		_("Department") + ":Data:120",
		_("Designation") + ":Data:120",
		_("Region") + ":Data:120",
		_("From Date") + ":Data:120",
		_("To Date") + ":Data:120",
		_("Feedback/Status") + ":Data:120",
	]

def get_pending_attendance_requests(filters, user):
    
	conditions = ""

    # if filters.get("company"):
    #     conditions1 += " and company = %(company)s"
	if filters.get("department"):
		conditions += " and department = %(department)s"
	if filters.get("region"):
		conditions += " and region = %(region)s"
	if filters.get("date"):
		conditions += " and %(date)s between from_date  and to_date"

	if "HR Manager" in frappe.get_roles(user):
		query =""" 
                SELECT lr.employee_code, lr.employee_name, lr.department, lr.designation, lr.region, cast(lr.from_time as time) as from_time, cast(lr.to_time as time) as to_time, lr.from_date, lr.reason, lr.status
                FROM `tabAttendance Request` lr
                WHERE lr.docstatus = 0 {condition}
                order by to_date desc  """.format(condition = conditions)
        # Database
		result = frappe.db.sql(query, filters)
	else:
		query =""" 
    			SELECT lr.employee_code, lr.employee_name, lr.department, lr.designation, lr.region, cast(lr.from_time as time) as from_time, cast(lr.to_time as time) as to_time, lr.from_date, lr.reason, lr.status
        		FROM `tabAttendance Request` lr, `tabUser Permission` per
        		WHERE lr.docstatus = 0 and lr.employee = per.for_value  and per.user='{id}' and per.allow='Employee'  {condition}
				group by lr.employee
        		order by to_date desc  """.format(id=user, condition = conditions)
		# Database
		result = frappe.db.sql(query, filters)
	return result

# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


# ---Pending Comp Off Requests @@@
def get_pending_comp_off_requests_columns():
	return [
		_("Employee Code") + ":Data:120",
		_("Employee name") + ":Data:120",
		_("Designation") + ":Data:120",
		_("Department") + ":Data:120",
		_("From Time") + ":Data:120",
		_("To Time") + ":Data:120",
		_("Applying Hours") + ":Data:120",
		_("Total Comp Off Balance") + ":Data:120",
		_("Feedback/Status") + ":Data:120",
	]
# 
def get_pending_comp_off_requests(filters, user):
	conditions = get_leave_condition(filters)
	if "HR Manager" in frappe.get_roles(user):
		query =""" 
        		SELECT comp.employeecode, comp.employee_name, comp.designation, comp.department, comp.applying_date, 
        		cast(comp.work_from as time) as work_from, cast(comp.work_to as time) as work_to, comp.applying_hours, comp.total_comp_off_balance, comp.status
        		FROM `tabComp Off` comp
        		WHERE comp.docstatus = 0 and comp.leave_type = 'Regular'
    			{condition}  
        		order by comp.posting_date desc  """.format(condition = conditions)
		# Database
		result = frappe.db.sql(query, filters)
	else:
		query =""" 
            	SELECT comp.employeecode, comp.employee_name, comp.designation, comp.department, comp.applying_date, 
            	cast(comp.work_from as time) as work_from, cast(comp.work_to as time) as work_to, comp.applying_hours, comp.total_comp_off_balance, comp.status
            	FROM `tabComp Off` comp, `tabUser Permission` per
            	WHERE comp.docstatus = 0 and comp.leave_type = 'Regular' 
            	and comp.employee=per.for_value and per.user='{id}' and per.allow='Employee'
            	{condition}
				group by comp.employee
            	order by posting_date desc  """.format(id=user, condition = conditions)
		# Database
		result = frappe.db.sql(query, filters)
	return result
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# Approved Comp Off @@@
def get_approved_comp_off_columns():
	return [
		_("Employee Code") + ":Data:120",
		_("Employee name") + ":Data:120",
		_("Designation") + ":/Department:120",
		_("Department") + ":Data:120",
		_("From Time") + ":Data:120",
		_("To Time") + ":Data:120",
		_("Applying Hours") + ":Data:120",
		_("Total Comp Off Balance") + ":Data:120",
		_("Feedback/Status") + ":Data:120",
	]

def get_approved_comp_off(filters, user):
	conditions = get_leave_condition(filters)
	if "HR Manager" in frappe.get_roles(user):
		query =""" 
        		SELECT employeecode, employee_name, designation, department, cast(work_from as time) as work_from, cast(work_to as time) as work_to, applying_hours,total_comp_off_balance, status 
        		FROM `tabComp Off`
        		WHERE docstatus=1 and leave_type = 'Regular' {condition}
        		order by work_from, work_to  """.format(condition = conditions)
		# Database
		result = frappe.db.sql(query, filters)
	else:
		query =""" 
				SELECT comp.employeecode, comp.employee_name, comp.designation, comp.department, cast(comp.work_from as time) as work_from, cast(comp.work_to as time) as work_to, comp.applying_hours,comp.total_comp_off_balance, comp.status 
            	FROM `tabComp Off` comp, `tabUser Permission` per
            	WHERE comp.docstatus=1 and comp.leave_type = 'Regular' 
            	and comp.employee=per.for_value and per.user='{id}' and per.allow='Employee' 
            	{condition}
				group by comp.employee
            	order by work_from, work_to  """.format(id=user, condition = conditions)
		# Database
		result = frappe.db.sql(query, filters)
	return result
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

# ---Approved Leaves @@@
def get_approved_leaves_columns():
	return [
		_("Employee Code") + ":Link/Employee:120",
		_("Employee name") + ":Data:120",
		_("Department") + ":Data:120",
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
				SELECT employee_code, employee_name, department, designation,from_date,to_date, total_leave_days, leave_type
				FROM `tabLeave Application`
				WHERE docstatus= 1 and status='Approved' {condition}  
				order by posting_date desc  """.format(condition = conditions)
		# Database
		result = frappe.db.sql(query, filters)
	else:
		query =""" 
                SELECT la.employee_code, la.employee_name, la.department, la.designation,la.from_date,la.to_date, la.total_leave_days, la.leave_type
                FROM `tabLeave Application` la, `tabUser Permission` per
                WHERE la.docstatus= 1 and la.status='Approved' 
                and la.employee=per.for_value and per.user='{id}' and per.allow='Employee'
                {condition}
				group by la.employee
                order by la.posting_date desc  """.format(id=user, condition = conditions)
		result = frappe.db.sql(query, filters)
	return result
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


#---Processing-Ending---##############################################################

###########################################
# Filter data condtions
def get_attendance_condition(filters):

    conditions1 = ""

    # if filters.get("company"):
    #     conditions1 += " and company = %(company)s"
    if filters.get("department"):
        conditions1 += " and department = %(department)s"
    if filters.get("region"):
        conditions1 += " and custom_region = %(region)s"
    if filters.get("date"):
        conditions1 += " and attendance_date = %(date)s"
    return conditions1

# Filter data condtions
def get_leave_condition(filters):

    conditions2 = ""
    # if filters.get("company"):
    #     conditions2 += " and company = %(company)s"
    if filters.get("department"):
        conditions2 += " and department = %(department)s"
    if filters.get("region"):
        conditions2 += " and region = %(region)s"
    if filters.get("date"):
        conditions2 += " and posting_date =%(date)s "
    return conditions2
