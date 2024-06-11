import frappe, ast
from frappe.utils import date_diff

@frappe.whitelist()
def fetch_counts(filters):
    filters = ast.literal_eval(filters)
    # 
    head_count = get_head_counts(filters)
    presents = get_presents_late_comings_in_times_average_late_coming(filters)
    absents = get_absents_and_absenteeism(filters, head_count, presents)
    leaves = get_short_unapproved_leaves(filters)
    contract = get_contract_completion(filters)
    probation = get_probation_completion(filters)
    return {
        "head_count": head_count,
        "presents": presents,
        "absents": absents,
        "leaves": leaves,
        "contract": contract,
        "probation": probation,
        "avg_overtime": get_avg_overtime_hours(filters),
    }

def get_head_counts(filters):
    query = """ 
        Select count(name) 
        From `tabEmployee`
        Where 
            status="Active"
            and (ifnull(relieving_date, "")="" || relieving_date>=curdate())
     """
    query += " and company = %(company)s " if(filters.get("company")) else ""
    query += " and branch = %(branch)s " if(filters.get("branch")) else ""
    r = frappe.db.sql(query, filters)
    return r[0][0] if(r) else 0

def get_presents_late_comings_in_times_average_late_coming(filters):
    query = """ 
        Select count(att.name) as total,
            ifnull(sum(case when late_entry=1 then 1 else 0 end)) as late_comings
        From `tabAttendance` att inner join `tabEmployee` e on (att.employee=e.name)
        Where att.docstatus=1
        and att.status in ("Present", "Work From Home")
        and (ifnull(e.relieving_date, "")="" || e.relieving_date>=curdate())"""
    query += " and att.company = %(company)s " if(filters.get("company")) else ""
    query += " and att.custom_branch = %(branch)s " if(filters.get("branch")) else ""
    query += "and att.attendance_date between %(from_date)s and %(to_date)s " if(filters.get('from_date') and filters.get('to_date')) else ""
    r = frappe.db.sql(query, filters, as_dict=1)
    if(r):
        data = r[0]
        data["in_times"] = data["total"]
        data["average_late_coming"] = round((data["late_comings"]/data["total"]) * 100)
        return data
    return {}

def get_absents_and_absenteeism(filters, head_count, presents):
    total_head_count = head_count * (date_diff(filters.get("to_date"), filters.get("from_date")) + 1)
    total_absents = 0
    average = 0
    if(presents):
        ptotal = presents.total
        total_holidays = get_holidays(filters)
        ph = (ptotal+total_holidays)
        total_absents = (total_head_count-ph) if(total_head_count>ph) else 0
        average = round((total_absents/total_head_count) * 100)
    return {
        "total": total_absents,
        "average": average
    }

def get_holidays(filters):
    query = """
        Select count(h.name) as total_holidays
        From `tabHoliday` h Inner Join `tabEmployee` e ON (h.parent = e.holiday_list)
        Where e.status="Active" and (ifnull(e.relieving_date, "")="" || e.relieving_date>=CURRENT_DATE())
    """
    query += " and e.company = %(company)s " if(filters.get("company")) else ""
    query += " and e.branch = %(branch)s " if(filters.get("branch")) else ""
    query += "and h.holiday_date between %(from_date)s and %(to_date)s " if(filters.get('from_date') and filters.get('to_date')) else ""
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
    r = frappe.db.sql(query, filters)
    return r[0][0] if(r) else 0

def get_avg_overtime_hours(filters):
    query = """ 
        Select 
            SEC_TO_TIME(SUM(TIME_TO_SEC(att.custom_overtime_hours))) as total_overtime
        From 
            `tabAttendance` att inner join `tabEmployee` e on (att.employee=e.name)
        Where 
            att.docstatus=1
            and att.status in ("Present", "Work From Home")
            and (ifnull(e.relieving_date, "")="" || e.relieving_date>=curdate())
    """
    query += " and e.company = %(company)s " if(filters.get("company")) else ""
    query += " and e.custom_branch = %(branch)s " if(filters.get("branch")) else ""
    query += "and att.attendance_date between %(from_date)s and %(to_date)s " if(filters.get('from_date') and filters.get('to_date')) else ""
    r = frappe.db.sql(query, filters, as_dict=0)
    return str(r[0][0]).split(".")[0] if(r) else 0

""" Here charts API """

@frappe.whitelist()
def get_charts(filters):
    filters = ast.literal_eval(filters)
    return {
        "department_wise": get_employee_count_by_department(filters),
        "salary_range": get_employee_count_by_salary_range(filters),
    }

def get_employee_count_by_department(filters):
    query = """ 
        Select (department)as name, count(name) as y 
        From `tabEmployee`
        Where 
            status="Active"
            and ifnull(department, "") != ""
            and (ifnull(relieving_date, "")="" || relieving_date>=curdate())
     """
    query += " and company = %(company)s " if(filters.get("company")) else ""
    query += " and branch = %(branch)s " if(filters.get("branch")) else ""
    query += " Group By department"
    query += " Order By y"
    r = frappe.db.sql(query, filters, as_dict=1)
    return r

def get_employee_count_by_salary_range(filters):
    query = """ 
        Select 
            ifnull(sum(case when (base between 0 and 50000) then 1 else 0 end),0) as "0-50,000",
            ifnull(sum(case when (base between 50001 and 100000) then 1 else 0 end),0) as "50,001-100,000",
            ifnull(sum(case when (base between 100001 and 150000) then 1 else 0 end),0) as "100,001-150,000",
            ifnull(sum(case when (base between 150001 and 200000) then 1 else 0 end),0) as "150,001-200,000",
            ifnull(sum(case when (base between 200001 and 250000) then 1 else 0 end),0) as "200,001-250,000",
            ifnull(sum(case when (base between 250001 and 300000) then 1 else 0 end),0) as "250,001-300,000",
            ifnull(sum(case when (base between 300001 and 400000) then 1 else 0 end),0) as "300,001-400,000"

        From `tabEmployee` e Inner Join `tabSalary Structure Assignment` s ON (e.name=s.employee)
        Where 
            e.status="Active"
            and ifnull(e.department, "") != ""
            and (ifnull(e.relieving_date, "")="" || e.relieving_date>=curdate())
     """
    query += " and e.company = %(company)s " if(filters.get("company")) else ""
    query += " and e.branch = %(branch)s " if(filters.get("branch")) else ""
    # query += " Group By base"
    r = frappe.db.sql(query, filters, as_dict=1)
    salary_ranges = []
    for d in r:
        for key, value in d.items():
            salary_ranges.append({
                "name": key,
                "y": value
            })
    return salary_ranges