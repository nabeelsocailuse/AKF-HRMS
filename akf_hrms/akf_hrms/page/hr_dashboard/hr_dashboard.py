import frappe, ast
from frappe.utils import date_diff
import json

@frappe.whitelist()
@frappe.whitelist()
def get_hr_counts(filters):
    filters = ast.literal_eval(filters)
    # 
    head_count = get_head_counts(filters)
    presents = total_present(filters)
    total_absent = total_absent_count(filters)
    absenteesim = get_absents_and_absenteeism(filters, head_count, presents)
    late_comings = get_late_comings_count(filters)
    in_time = get_in_time_count(filters)
    avg_late_coming = get_average_late_coming(filters)
    leaves = get_short_unapproved_leaves(filters)
    in_station = get_in_station_leaves(filters)
    out_station = get_out_station_leaves(filters)
    contract = get_contract_completion(filters)
    probation = get_probation_completion(filters)
    

    return {
        "head_count": head_count,
        "presents": presents,
        "total_absent": total_absent,
        "absenteesim": absenteesim,
        "late_comings": late_comings,
        "in_time": in_time,
        "avg_late_coming": avg_late_coming,
        "leaves": leaves,
        "in_station": in_station,
        "out_station": out_station,
        "contract": contract,
        "avg_overtime": get_avg_overtime_hours(filters),
        "probation": probation,
        "department_list": get_department_list(filters),
    }

# def get_head_counts(filters):
#     query = """ 
#         Select count(name) 
#         From `tabEmployee`
#         Where 
#             status="Active"
#             and (ifnull(relieving_date, "")="" || relieving_date>=curdate())
#      """
#     # query += " AND relieving_date BETWEEN %(from_date)s AND %(to_date)s" if (filters.get('from_date') and filters.get('to_date')) else ""
#     query += " and company = %(company)s " if(filters.get("company")) else ""
#     query += " and branch = %(branch)s " if(filters.get("branch")) else ""
#     r = frappe.db.sql(query, filters)
#     return r[0][0] if(r) else 0

def get_head_counts(filters):
    query = """ 
        SELECT count(name) 
        FROM `tabEmployee`
        WHERE 
            status="Active"
            AND (ifnull(relieving_date, "") = "" OR relieving_date > %(to_date)s)
     """
    query += " AND company = %(company)s" if filters.get("company") else ""
    query += " AND branch = %(branch)s" if filters.get("branch") else ""
    
    r = frappe.db.sql(query, filters)
    return r[0][0] if r else 0


# def total_present(filters):
#     query = """ 
#             SELECT count(att.name)
#             FROM `tabAttendance` as att 
#             INNER JOIN `tabEmployee` as e ON att.employee = e.name
#             WHERE att.status IN ("Present", "Work From Home")
#             AND att.docstatus = 1
#             AND (ifnull(e.relieving_date, "") = "" OR e.relieving_date >= curdate())
#         """
#     query += " AND att.company = %(company)s" if filters.get("company") else ""
#     query += " AND att.custom_branch = %(branch)s" if filters.get("branch") else ""
#     query += " AND att.attendance_date BETWEEN %(from_date)s AND %(to_date)s" if (filters.get('from_date') and filters.get('to_date')) else ""
    
#     r = frappe.db.sql(query, filters)
#     return r[0][0] if r else 0


def total_present(filters):
    query = """ 
            SELECT count(att.name)
            FROM `tabAttendance` as att 
            INNER JOIN `tabEmployee` as e ON att.employee = e.name
            WHERE att.status IN ("Present", "Work From Home")
            AND att.docstatus = 1
            AND (ifnull(e.relieving_date, "") = "" OR e.relieving_date >= %(to_date)s)
        """
    query += " AND att.company = %(company)s" if filters.get("company") else ""
    query += " AND att.custom_branch = %(branch)s" if filters.get("branch") else ""
    query += " AND att.attendance_date BETWEEN %(from_date)s AND %(to_date)s" if (filters.get('from_date') and filters.get('to_date')) else ""
    
    r = frappe.db.sql(query, filters)
    return r[0][0] if r else 0


def total_absent_count(filters):
    query = """ 
            SELECT count(att.name)
            FROM `tabAttendance` as att 
            INNER JOIN `tabEmployee` as e ON att.employee = e.name
            WHERE att.status = 'Absent'
            AND att.docstatus = 1
            AND (ifnull(e.relieving_date, "") = "" OR e.relieving_date > %(to_date)s)

        """
    query += " AND att.company = %(company)s" if filters.get("company") else ""
    query += " AND att.custom_branch = %(branch)s" if filters.get("branch") else ""
    query += " AND att.attendance_date BETWEEN %(from_date)s AND %(to_date)s" if (filters.get('from_date') and filters.get('to_date')) else ""
    frappe.msgprint(f"absent query: {query}")
    r = frappe.db.sql(query, filters)
    frappe.msgprint(f"absent result: {r}")
    return r[0][0] if(r) else 0

def get_late_comings_count(filters):
    query = """ 
        SELECT count(name)
        FROM `tabAttendance`
        WHERE late_entry = 1
        AND docstatus = 1
        AND status IN ("Present", "Work From Home")
    """
    if filters.get("company"):
        query += " AND company = %(company)s"
    if filters.get("branch"):
        query += " AND custom_branch = %(branch)s"
    if filters.get('from_date') and filters.get('to_date'):
        query += " AND attendance_date BETWEEN %(from_date)s AND %(to_date)s"
        
    r = frappe.db.sql(query, filters)
    return r[0][0] if r else 0

# def get_in_station_leaves(filters):
#     query = """ 
#         SELECT count(name)
#         FROM `tabLeave Application`
#         WHERE leave_type = 'Official Duty (In-Station)'
#         and custom_approval_status = 'Approved'
#         and docstatus = 1
#     """
#     print("Station Leavesss")
    
#     if filters.get("company"):
#         query += " AND company = %(company)s"
#     if filters.get("branch"):
#         query += " AND custom_branch = %(branch)s"
#     if filters.get('from_date') and filters.get('to_date'):
#         query += " AND posting_date BETWEEN %(from_date)s AND %(to_date)s"
        
#     r = frappe.db.sql(query, filters)
#     print(r)
#     return r[0][0] if r else 0


def get_in_station_leaves(filters):
    query = """ 
        SELECT count(name)
        FROM `tabLeave Application`
        WHERE leave_type = 'Official Duty (In-Station)'
        AND custom_approval_status = 'Approved'
        AND docstatus = 1
    """
    print("Station Leaves")

    if filters.get("company"):
        query += " AND company = %(company)s"
    if filters.get("branch"):
        query += " AND custom_branch = %(branch)s"
    if filters.get('from_date') and filters.get('to_date'):
        query += " AND (from_date <= %(to_date)s AND to_date >= %(from_date)s)"

    print("Query:", query)
    print("Filters:", filters)
    
    r = frappe.db.sql(query, filters)
    print("Result:", r)
    return r[0][0] if r else 0

def get_out_station_leaves(filters):
    query = """ 
        SELECT count(name)
        FROM `tabLeave Application`
        WHERE leave_type = 'Official Duty (Out-Station)'
        and custom_approval_status = 'Approved'
    """
    print("Station Leavesss")
    print(query)
    
    if filters.get("company"):
        query += " AND company = %(company)s"
    if filters.get("branch"):
        query += " AND custom_branch = %(branch)s"
    if filters.get('from_date') and filters.get('to_date'):
        query += " AND (from_date <= %(to_date)s AND to_date >= %(from_date)s)"
        
    r = frappe.db.sql(query, filters)
    print(r)
    return r[0][0] if r else 0

def get_in_time_count(filters):
    query = """ 
        SELECT count(name)
        FROM `tabAttendance`
        WHERE late_entry = 0
        AND docstatus = 1
        AND status IN ("Present", "Work From Home")
    """
    if filters.get("company"):
        query += " AND company = %(company)s"
    if filters.get("branch"):
        query += " AND custom_branch = %(branch)s"
    if filters.get('from_date') and filters.get('to_date'):
        query += " AND attendance_date BETWEEN %(from_date)s AND %(to_date)s"
        
    r = frappe.db.sql(query, filters)
    return r[0][0] if r else 0

def get_absents_and_absenteeism(filters, head_count, presents):
    total_head_count = head_count * (date_diff(filters.get("to_date"), filters.get("from_date")) + 1)
    total_holidays = head_count * get_holidays(filters)
    # 
    total_absents = total_absent_count(filters)
    average = 0

    if(presents):  # Check if presents is provided
        ptotal = presents  # presents is an integer
        ph = ptotal + total_holidays
        total_absents = total_head_count - ph if (total_head_count > ph) else 0
        # Ensure total_head_count is not zero before division
    else:
        total_absents = total_head_count
        average = average

    if (total_head_count>0): average = round((total_absents / total_head_count) * 100)

    return {
        "total": total_absents,
        "average": average
    }

def get_average_late_coming(filters):
    query = """ 
        SELECT COUNT(att.name) AS total,
            IFNULL(SUM(CASE WHEN late_entry = 1 THEN 1 ELSE 0 END), 0) AS late_comings
        FROM `tabAttendance` att INNER JOIN `tabEmployee` e ON (att.employee=e.name)
        WHERE att.docstatus = 1
        AND att.status IN ("Present", "Work From Home")
        AND (IFNULL(e.relieving_date, "") = "" OR e.relieving_date >= CURDATE())"""
    query += " AND att.company = %(company)s" if filters.get("company") else ""
    query += " AND att.custom_branch = %(branch)s" if filters.get("branch") else ""
    query += " AND att.attendance_date BETWEEN %(from_date)s AND %(to_date)s" if (filters.get('from_date') and filters.get('to_date')) else ""
    
    # print("Averageee Late Cominggg!")
    # print("Query:", query)  # Debug print
    
    r = frappe.db.sql(query, filters, as_dict=1)
    # print("Result:", r)  # Debug print
    
    if r:
        data = r[0]
        if data["total"] > 0:
            average_late_coming = round((data["late_comings"] / data["total"]) * 100)
        else:
            average_late_coming = 0
    return average_late_coming

def get_holidays(filters):
    query = """
        Select count(h.name) as total_holidays
        From `tabHoliday` h Inner Join `tabEmployee` e ON (h.parent = e.holiday_list)
        Where e.status="Active" and (ifnull(e.relieving_date, "")="" || e.relieving_date>=CURRENT_DATE())
    """
    query += " and e.company = %(company)s " if(filters.get("company")) else ""
    query += " and e.branch = %(branch)s " if(filters.get("branch")) else ""
    query += "and h.holiday_date between %(from_date)s and %(to_date)s " if(filters.get('from_date') and filters.get('to_date')) else ""
    query += "GROUP BY e.name"
    r = frappe.db.sql(query, filters)
    return r[0][0] if(r) else 0

def get_short_unapproved_leaves(filters):
    query = """ 
        Select 
            ifnull(sum(case when (la.docstatus<2 and la.half_day=1) then 1 else 0 end),0) as short_leaves,
            ifnull(sum(case when (la.docstatus<2 and la.status in ("Open")) then 1 else 0 end),0) as unapproved_leaves

        From `tabLeave Application` la Inner Join `tabEmployee` e ON (la.employee=e.name)
        Where la.docstatus<2
        and la.status in ("Open", "Approved")
        AND (IFNULL(e.relieving_date, "") = "" OR e.relieving_date >= CURDATE())
        
    """
    query += " and la.company = %(company)s " if(filters.get("company")) else ""
    query += " and e.branch = %(branch)s " if(filters.get("branch")) else ""
    query += "and (la.from_date>=%(from_date)s and la.to_date<=%(to_date)s) " if(filters.get('from_date') and filters.get('to_date')) else ""
    r = frappe.db.sql(query, filters, as_dict=1)
    return r[0] if(r) else {}


def get_in_staitons_and_out_station(filters):
    pass

def get_contract_completion(filters):
    query = """ 
        Select count(name) 
        From `tabEmployee`
        Where 
            status="Active"
            and (ifnull(relieving_date, "")="" || relieving_date>=curdate())
            and (ifnull(contract_end_date, "")!="" || contract_end_date<curdate())
     """
    query += " and company = %(company)s " if(filters.get("company")) else ""
    query += " and branch = %(branch)s " if(filters.get("branch")) else ""
    query += "and (contract_end_date>=%(from_date)s and contract_end_date<=%(to_date)s) " if(filters.get('from_date') and filters.get('to_date')) else ""
    r = frappe.db.sql(query, filters)
    return r[0][0] if(r) else 0

def get_probation_completion(filters):
    query = """ 
        Select count(name) 
        From `tabEmployee`
        Where 
            status="Active"
            and (ifnull(relieving_date, "")="" || relieving_date>=curdate())
            and (ifnull(final_confirmation_date, "")!="" || final_confirmation_date<curdate())
     """
    query += " and company = %(company)s " if(filters.get("company")) else ""
    query += " and branch = %(branch)s " if(filters.get("branch")) else ""
    query += "and (final_confirmation_date>=%(from_date)s and final_confirmation_date<=%(to_date)s) " if(filters.get('from_date') and filters.get('to_date')) else ""
    r = frappe.db.sql(query, filters)
    return r[0][0] if(r) else 0

def get_avg_overtime_hours(filters):
    query = """ 
        SELECT 
            SEC_TO_TIME(SUM(TIME_TO_SEC(att.custom_overtime_hours))) AS total_overtime
        FROM 
            `tabAttendance` att 
        INNER JOIN 
            `tabEmployee` e ON att.employee = e.name
        WHERE 
            att.docstatus = 1
            AND att.status IN ('Present', 'Work From Home')
            AND (IFNULL(e.relieving_date, '') = '' OR e.relieving_date >= CURDATE())
    """
    if filters.get('company'):
        query += " AND e.company = %(company)s "
    if filters.get('branch'):
        query += " AND e.branch = %(branch)s "
    if filters.get('from_date') and filters.get('to_date'):
        query += " AND att.attendance_date BETWEEN %(from_date)s AND %(to_date)s "

    r = frappe.db.sql(query, filters, as_dict=0)
    return str(r[0][0]).split(".")[0] if r and r[0][0] else "0"

@frappe.whitelist()
# HR Dashboard Chart API
def get_hr_charts(filters):
    filters = ast.literal_eval(filters)
    return {
        "department_wise": get_employee_count_by_department(filters),
        "salary_range": get_employee_count_by_salary_range(filters),
        "count_by_employment_type": count_by_employment_type(filters),
        "employee_check_in_and_late_entry": employee_check_in_and_late_entry(filters)
    }

""" HR Charts API """
# 1- HR Dashboard Chart
def get_employee_count_by_department(filters):
    query = """ 
        SELECT department as name, COUNT(name) as y 
        FROM `tabEmployee`
        WHERE 
            status = "Active"
            AND IFNULL(department, "") != ""
            AND (IFNULL(relieving_date, "") = "" OR relieving_date >= CURDATE())
    """
    query += " AND company = %(company)s " if filters.get("company") else ""
    query += " AND branch = %(branch)s " if filters.get("branch") else ""
    query += " GROUP BY department"
    query += " ORDER BY y"
    r = frappe.db.sql(query, filters, as_dict=1)
    return r
# 2- HR Dashboard Chart
def get_employee_count_by_salary_range(filters):
    query = """ 
        SELECT 
            IFNULL(SUM(CASE WHEN (latest_salary.base BETWEEN 0 AND 50000) THEN 1 ELSE 0 END), 0) AS "0-50,000",
            IFNULL(SUM(CASE WHEN (latest_salary.base BETWEEN 50001 AND 100000) THEN 1 ELSE 0 END), 0) AS "50,001-100,000",
            IFNULL(SUM(CASE WHEN (latest_salary.base BETWEEN 100001 AND 150000) THEN 1 ELSE 0 END), 0) AS "100,001-150,000",
            IFNULL(SUM(CASE WHEN (latest_salary.base BETWEEN 150001 AND 200000) THEN 1 ELSE 0 END), 0) AS "150,001-200,000",
            IFNULL(SUM(CASE WHEN (latest_salary.base BETWEEN 200001 AND 250000) THEN 1 ELSE 0 END), 0) AS "200,001-250,000",
            IFNULL(SUM(CASE WHEN (latest_salary.base BETWEEN 250001 AND 300000) THEN 1 ELSE 0 END), 0) AS "250,001-300,000",
            IFNULL(SUM(CASE WHEN (latest_salary.base BETWEEN 300001 AND 400000) THEN 1 ELSE 0 END), 0) AS "300,001-400,000"
        FROM `tabEmployee` e 
        INNER JOIN (
            SELECT 
                s.employee,
                MAX(s.from_date) as latest_from_date
            FROM `tabSalary Structure Assignment` s
            WHERE s.docstatus = 1
            GROUP BY s.employee
        ) latest_assignment ON e.name = latest_assignment.employee
        INNER JOIN `tabSalary Structure Assignment` latest_salary 
            ON latest_assignment.employee = latest_salary.employee 
            AND latest_assignment.latest_from_date = latest_salary.from_date
        WHERE 
            e.status = "Active"
            AND IFNULL(e.department, "") != ""
            AND (IFNULL(e.relieving_date, "") = "" OR e.relieving_date >= CURDATE())
            AND latest_salary.docstatus = 1
    """
    
    if filters.get("company"):
        query += " AND e.company = %(company)s "
    
    if filters.get("branch"):
        query += " AND e.branch = %(branch)s "

    r = frappe.db.sql(query, filters, as_dict=1)
    
    salary_ranges = []
    for d in r:
        for key, value in d.items():
            salary_ranges.append({
                "name": key,
                "y": value
            })
    
    return salary_ranges
# 3- HR Dashboard Chart
def employee_check_in_and_late_entry(filters):
    query = """
        SELECT
            CASE
                WHEN late_entry = 1 THEN 'Late'
                ELSE 'On-time'
            END AS entry_status,
            SUM(CASE WHEN late_entry = 1 THEN 1 ELSE 0 END) AS late_count,
            SUM(CASE WHEN late_entry = 0 THEN 1 ELSE 0 END) AS on_time_count
        FROM
            `tabAttendance`
        WHERE
            docstatus = 1
         AND status IN ("Present", "Work From Home")
    """
    
    if filters.get("company"):
        query += " AND company = %(company)s "
    if filters.get("branch"):
        query += " AND custom_branch = %(branch)s "
    if filters.get('from_date') and filters.get('to_date'):
        query += " AND attendance_date BETWEEN %(from_date)s AND %(to_date)s "
        
    query += """
        GROUP BY entry_status
        ORDER BY entry_status
    """
    
    result = frappe.db.sql(query, filters, as_dict=True)
    return result

# 4- HR Dashboard Chart
def count_by_employment_type(filters):
    query = """
       SELECT COUNT(name) as total, employment_type as name
        FROM `tabEmployee` 
        WHERE status = 'Active'
    """

    query_params = {}

    if filters.get("company"):
        query += " AND company = %(company)s "
        query_params["company"] = filters["company"]
    
    if filters.get("branch"):
        query += " AND branch = %(branch)s "
        query_params["branch"] = filters["branch"]

    query += " GROUP BY employment_type"

    r = frappe.db.sql(query, query_params, as_dict=1)

    data = [{'name': d['name'], 'y': d['total']} for d in r]
    
    return data

""" HR Recruitment Dashboard Counts"""
@frappe.whitelist()
def get_recruitement_counts(filters):
    filters = ast.literal_eval(filters)
    return {
        "total_applicants": get_total_applicants(filters),
        "shortlisted_candidates": get_shortlisted_candidates(filters),
        "hired_candidates": get_hired_candidates(filters),
        "rejected_candidates": get_rejected_candidates(filters),
        "time_to_fill": get_time_to_fill(filters)
    }

def get_department_list(filters):
    query = '''
        SELECT name 
        FROM `tabDepartment` 
        WHERE docstatus = 0
    '''
    
    if filters.get("company"):
        query += " AND company = %(company)s "
    departments = frappe.db.sql(query, filters, as_dict=True)
    
    options = ""
    for department in departments:
        options += "<option value='%s'>%s</option>" % (department.name, department.name)
    
    return options

@frappe.whitelist()
def get_total_applicants(filters):
    query = """
        SELECT IFNULL(COUNT(ja.name), 0) as total
        FROM `tabJob Applicant` as ja
        INNER JOIN `tabJob Opening` as jo ON ja.job_title = jo.name
        WHERE ja.docstatus=0
        -- ja.status = 'Open'
    """
    if(filters.get("company")):
        query += " AND ja.custom_company = %(company)s"    
    if(filters.get("department")):
        query += " AND ja.custom_department = %(department)s"    
    
    result = frappe.db.sql(query, filters, as_dict=False)
    return result[0][0] if(result) else 0
  
@frappe.whitelist()
def get_shortlisted_candidates(filters):
    query = """
        SELECT IFNULL(COUNT(ja.name), 0) as total
        FROM `tabJob Applicant` AS ja
        WHERE ja.status IN ('Hold', 'Replied')
    """
    if filters.get("company"):
        query += " AND ja.custom_company = %(company)s "
    if filters.get("department"):
        query += " AND ja.custom_department = %(department)s "
    result = frappe.db.sql(query, filters, as_dict=False)

    return result[0][0] if(result) else 0

@frappe.whitelist()
def get_hired_candidates(filters):
    query = """
            SELECT IFNULL(COUNT(ja.name), 0) as total
            FROM `tabJob Applicant` as ja
        WHERE ja.status = 'Accepted'
    """
    if filters.get("company"):
        query += " AND ja.custom_company = %(company)s "
    if filters.get("department"):
        query += " AND ja.custom_department = %(department)s "
    result = frappe.db.sql(query, filters, as_dict=False)

    return result[0][0] if(result) else 0
    
@frappe.whitelist()
def get_rejected_candidates(filters):
    query = """
            SELECT IFNULL(COUNT(ja.name), 0) as total
        FROM `tabJob Applicant` as ja
        WHERE ja.status = 'Rejected'
    """
    if filters.get("company"):
        query += " AND ja.custom_company = %(company)s "
    if filters.get("department"):
        query += " AND ja.custom_department = %(department)s "
    result = frappe.db.sql(query, filters, as_dict=False)

    return result[0][0] if(result) else 0
    
@frappe.whitelist()
def get_time_to_fill(filters):
    query = """
        SELECT AVG(TIMESTAMPDIFF(DAY, posting_date, completed_on)) AS avg_time_to_fill
        FROM `tabJob Requisition`
        WHERE status = 'Filled'
    """
    if filters.get("company"):
        query += " AND company = %(company)s "
    if filters.get("department"):
        query += " AND department = %(department)s"

    result = frappe.db.sql(query, filters, as_dict=True)

    if result and 'avg_time_to_fill' in result[0]:
        avg_time = result[0]['avg_time_to_fill']
        if avg_time is not None:
            return round(avg_time, 2)
        else:
            return 0
    return 0

# Recruitment Dashboard API
@frappe.whitelist()
def get_recruitement_charts(filters):
    filters = ast.literal_eval(filters)
    return {
        "open_position_by_dept": open_position_by_dept(filters),
        "applications_received_by_source": applications_received_by_source(filters),
    }
# 1- Recruitment Dashboard Chart
def open_position_by_dept(filters):
    query = """
        SELECT COUNT(name) as count, department as name
        FROM `tabJob Opening` 
        WHERE status = 'Open'
    """
    
    if filters.get("company"):
        query += " AND company = %(company)s "
    if filters.get("department"):
        query += " AND department = %(department)s "
    
    query += " GROUP BY department"
    
    r = frappe.db.sql(query, filters, as_dict=1)
    
    data = [{'name': d['name'], 'y': d['count']} for d in r]
    
    return data
# 2- Recruitment Dashboard Chart
def applications_received_by_source(filters):
    query = """
       SELECT COUNT(name) as count, source as name
        FROM `tabJob Applicant` 
    """
    
    if filters.get("company"):
        query += " WHERE custom_company = %(company)s "
    if filters.get("department"):
        query += " AND custom_department = %(department)s "
    
    query += " GROUP BY source"
    
    r = frappe.db.sql(query, filters, as_dict=1)
    data = [{'name': d['name'], 'y': d['count']} for d in r]
    
    return data
