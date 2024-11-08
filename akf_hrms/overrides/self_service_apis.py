import frappe

from frappe.utils import today
from datetime import datetime, timedelta

@frappe.whitelist()
def get_employee_dependents():				#Mubashir Bashir
    user_id = frappe.session.user
    
    employee = frappe.db.get_all('Employee', filters={'user_id': user_id}, fields=['name'])

    if not employee:
        return []

    employee_name = employee[0].get('name')

    dependents = frappe.db.get_all(
        'Employee Dependents',
        filters={'parent': employee_name},
        fields=['dependent_name', 'mobile_number', 'relation', 'cnic'],
		limit = 2
    )

    return dependents


@frappe.whitelist()
def get_employee_details():
	user_id = frappe.session.user
	employee = frappe.db.get_all('Employee', filters={'user_id': user_id}, fields=['name', 'first_name', 'branch', 'designation', 'department' , 'image', 'date_of_birth', 'date_of_joining', 'custom_cnic', 'employment_type', 'gender', 'custom_reports_to_line_manager_name'])
	
	if employee:
	
		emp_details = employee[0]

		# Fetch education levels for the employee
		education_records = frappe.db.get_all('Employee Education', filters={'parent': emp_details.name}, fields=['qualification', 'year_of_passing'], order_by='year_of_passing desc', limit=1)

		latest_qualification = None
		if education_records:
			latest_qualification = education_records[0].qualification

		return {
			"first_name": emp_details.first_name,
			"branch": emp_details.branch,
			"designation": emp_details.designation,
			"department": emp_details.department,
			"user": user_id,
			"image": emp_details.image,
			"date_of_birth": emp_details.date_of_birth,
			"date_of_joining": emp_details.date_of_joining,
			"cnic": emp_details.custom_cnic,
			"gender":emp_details.gender,
			"employment_type":emp_details.employment_type,
			"custom_reports_to_line_manager_name": emp_details.custom_reports_to_line_manager_name,
            "latest_education_level": latest_qualification if latest_qualification else "No education record"
        }
	else:
		return {
			"message": "No record exists."
		}


@frappe.whitelist()
def get_employee_date():
    user_id = frappe.session.user
    employee = frappe.db.get_all('Employee', filters={'user_id': user_id}, fields=['name'])
    
    if employee:
      
        name = employee[0]['name']  
        return {
            "name": name,
            "date": today()  
        }
    else:
         return {
            "message": "No Leave Record exists."
        }



@frappe.whitelist()
def get_attendance_logs_when_no_attendance():  # Mubashir Bashir
    user_id = frappe.session.user
    employee = frappe.db.get_all('Employee', filters={'user_id': user_id}, fields=['name'])

    if employee:
        employee_name = employee[0].name
        today = datetime.now()
        
        # Calculate the start_date (from_date)
        day = today.day
        if day > 20:
            start_date = datetime(today.year, today.month, 21)
        else:
            if today.month == 1:  # Handle January edge case
                start_date = datetime(today.year - 1, 12, 21)
            else:
                start_date = datetime(today.year, today.month - 1, 21)
				

        start_date = start_date.date()  

        attendance_logs = frappe.db.sql(
            """
            SELECT attendance_date 
            FROM `tabAttendance`
            WHERE employee = %s 
            AND attendance_date BETWEEN %s AND %s 
            AND docstatus = 1 
            AND status IN ('Present', 'Half Day', 'Work From Home') 
            AND ((in_time IS NULL AND out_time IS NOT NULL) OR (out_time IS NULL AND in_time IS NOT NULL))
            """,
            (employee_name, start_date, today),
            as_dict=True
        )
        
        attended_dates = {log.attendance_date for log in attendance_logs}
        
        request_statuses_to_exclude = [
            'Pending', 
            'Approved by the Line Manager', 
            'Approved by the Head of Department'
        ]

        pending_request_dates = frappe.db.get_all(
            "Attendance Request",
            filters={
                'employee': employee_name,
                'custom_approval_status': ['in', request_statuses_to_exclude],
                'from_date': ['between', [start_date, today]]
            },
            fields=['from_date']
        )
        pending_dates_set = {request.from_date for request in pending_request_dates}
        
        missing_attendance_dates = [
            date for date in attended_dates
            if date not in pending_dates_set
        ]
        
        # limited_missing_dates = missing_attendance_dates[-5:]  
        formatted_dates = [date for date in missing_attendance_dates]

        if not formatted_dates:
            return {"message": "All attendance marked for the last 30 days."}
        else:
            return {"missing_attendance_dates": formatted_dates}
    else:
        return {"message": "Employee not found."}

@frappe.whitelist()
def get_late_entry_dates(): 	# Mubashir Bashir
    user_id = frappe.session.user
    employee = frappe.db.get_all('Employee', filters={'user_id': user_id}, fields=['name'])

    if employee:
        employee_name = employee[0].name
        today = datetime.now().date()  

        if today.day > 20:
            start_date = datetime(today.year, today.month, 21).date()
        else:
            if today.month == 1:
                start_date = datetime(today.year - 1, 12, 21).date()
            else:
                start_date = datetime(today.year, today.month - 1, 21).date()

        attendance_logs = frappe.db.sql(
            """
            SELECT attendance_date 
            FROM `tabAttendance`
            WHERE employee = %s 
            AND attendance_date BETWEEN %s AND %s 
            AND docstatus = 1 
            AND late_entry = 1
            AND status IN ('Present', 'Half Day', 'Work From Home') 
            """,
            (employee_name, start_date, today),
            as_dict=True
        )

        attended_dates = {log.attendance_date for log in attendance_logs}

        if not attended_dates:
            return {"missing_attendance_dates": []}

        formatted_dates = list(attended_dates)
        return {"missing_attendance_dates": formatted_dates}

    else:
        return {"message": "Employee not found."}

@frappe.whitelist()
def get_early_exit_dates():  # Mubashir Bashir
    user_id = frappe.session.user
    employee = frappe.db.get_all('Employee', filters={'user_id': user_id}, fields=['name'])

    if employee:
        employee_name = employee[0].name
        today = datetime.now().date()  

        if today.day > 20:
            start_date = datetime(today.year, today.month, 21).date()
        else:
            if today.month == 1:
                start_date = datetime(today.year - 1, 12, 21).date()
            else:
                start_date = datetime(today.year, today.month - 1, 21).date()

        attendance_logs = frappe.db.sql(
            """
            SELECT attendance_date 
            FROM `tabAttendance`
            WHERE employee = %s 
            AND attendance_date BETWEEN %s AND %s 
            AND docstatus = 1 
            AND early_exit = 1
            AND status IN ('Present', 'Half Day', 'Work From Home') 
            """,
            (employee_name, start_date, today),
            as_dict=True
        )

        attended_dates = {log.attendance_date for log in attendance_logs}

        if not attended_dates:
            return {"missing_attendance_dates": []}

        formatted_dates = list(attended_dates)
        return {"missing_attendance_dates": formatted_dates}

    else:
        return {"message": "Employee not found."}


@frappe.whitelist()
def get_absent_days_dates():        #Mubashir Bashir
    import frappe
    from datetime import datetime, timedelta

    user_id = frappe.session.user
    employee = frappe.db.get_all('Employee', filters={'user_id': user_id, 'custom_no_attendance': 0}, fields=['name', 'holiday_list'])

    if employee:
        employee_name = employee[0].name
        employee_holiday_list = employee[0].holiday_list
        today = datetime.now().date() 
        
        if today.day > 20:
            start_date = datetime(today.year, today.month, 21).date()
        else:
            if today.month == 1: 
                start_date = datetime(today.year - 1, 12, 21).date()
            else:
                start_date = datetime(today.year, today.month - 1, 21).date()

        attendance_logs = frappe.db.sql("""
            SELECT attendance_date 
            FROM `tabAttendance`
            WHERE employee = %s 
            AND attendance_date BETWEEN %s AND %s 
            AND docstatus = 1
        """, (employee_name, start_date, today), as_dict=True)
        
        attended_dates = {log['attendance_date'] for log in attendance_logs}

        pending_request_statuses = ['Pending', 'Approved by the Line Manager', 'Approved by the Head of Department']
        pending_requests = frappe.db.get_all(
            "Attendance Request",
            filters={
                'employee': employee_name,
                'custom_approval_status': ['in', pending_request_statuses],
                'from_date': ['between', [start_date, today]]
            },
            fields=['from_date']
        )
        pending_dates_set = {request['from_date'] for request in pending_requests}

        holiday_dates = frappe.db.sql("""
            SELECT holiday_date 
            FROM `tabHoliday`
            WHERE parent = %(holiday_list)s
            AND holiday_date BETWEEN %(from_date)s AND %(to_date)s
        """, {"holiday_list": employee_holiday_list, "from_date": start_date, "to_date": today}, as_dict=True)
        
        holiday_dates_set = {h['holiday_date'] for h in holiday_dates}
        
        open_leaves = frappe.db.get_all(
            "Leave Application",
            filters={
                'employee': employee_name,
                'status': 'Open',
                'from_date': ['between', [start_date, today]]
            },
            fields=['from_date', 'to_date']
        )

        leave_dates_to_exclude = set()
        for leave in open_leaves:
            leave_from = leave['from_date']
            leave_to = leave['to_date']

            while leave_from <= leave_to:
                leave_dates_to_exclude.add(leave_from)
                leave_from += timedelta(days=1)

        all_dates = set(start_date + timedelta(days=i) for i in range((today - start_date).days + 1))

        absent_dates = [
            date for date in all_dates
            if date not in attended_dates
            and date not in pending_dates_set
            and date not in holiday_dates_set
            and date not in leave_dates_to_exclude
        ]

        # Return the list of absent dates
        if not absent_dates:
            return {"message": "All attendance marked for the last 30 days."}
        else:
            formatted_absent_dates = [date.strftime('%Y-%m-%d') for date in absent_dates]
            return {"absent_dates": formatted_absent_dates}
    else:
        return {"message": "Employee not found."}


@frappe.whitelist()
def get_employee_salary():			#Mubashir Bashir
	user_id = frappe.session.user
	employee = frappe.db.get_all('Employee', filters={'user_id': user_id}, fields=['name'])

	if not employee:
		return 0
	employee_name = employee[0].get('name')
	
	salary_structure = frappe.db.sql("""
		SELECT base 
		FROM `tabSalary Structure Assignment`
		WHERE employee = %s
		AND docstatus = 1 
		ORDER BY from_date DESC
		LIMIT 1
	""", (employee_name,), as_dict=True)

	if salary_structure:
		return salary_structure[0].get('base')
	else:
		return 0
	