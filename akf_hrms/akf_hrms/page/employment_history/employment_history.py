import frappe, json
from frappe.utils import formatdate, fmt_money, getdate, date_diff, time_diff_in_seconds, format_duration
@frappe.whitelist()
def get_information(filters):
    filters = json.loads(filters)
    # start, Nabeel Saleem, 19-12-2024
    verify_doc_permissions(filters)
    # end, Nabeel Saleem, 19-12-2024
    employee_detail = get_employee_details(filters)
    employee_history = get_employee_history(filters)
    hasEmployee = bool(employee_detail)

    data = {
        "hasEmployee": hasEmployee,
        "detail": employee_detail,
        "history": employee_history
    }

    return data

def verify_doc_permissions(filters):
    employee = filters.get('employee')
    doc = frappe.get_doc('Employee', employee)
    has_permission = frappe.has_permission('Employee', doc=doc , user=frappe.session.user)
    if(not has_permission): 
        frappe.throw(f"You don't have access to employee <b>{employee}</b>")
    
def get_employee_details(filters):
    result = frappe.db.sql("""
        SELECT
            CONCAT_WS(' ', emp.first_name, emp.middle_name, emp.last_name) as full_name,
            emp.designation as designation,
            emp.date_of_joining as date_of_joining,
            (select ifnull((base+ custom_mobile_allowance + custom_vehicle_allowance + custom_accomodation_allowance + custom_fuel_allowance + variable),0) from `tabSalary Structure Assignment` where docstatus=1 and employee=emp.name order by from_date desc limit 1) as current_salary,
            emp.custom_father_name as father_name,
            emp.department as department,
            emp.employment_type as employment_type,
            emp.custom_total_duration as total_duration,
            emp.cell_number as mobile_no,
            emp.image as image_url,
            GROUP_CONCAT(edu.qualification ORDER BY edu.idx SEPARATOR ', ') as qualification
        FROM
            `tabEmployee` emp
        LEFT JOIN
            `tabEmployee Education` edu ON emp.name = edu.parent
        WHERE
            emp.name = %(employee)s
        GROUP BY
            emp.name
    """, {"employee": filters.get('employee')}, as_dict=1)
    if(result):
        result[0]["date_of_joining"] = formatdate(result[0]["date_of_joining"])
        result[0]["current_salary"] = fmt_money(result[0]["current_salary"], precision=0, currency="PKR")
        result[0]["total_duration"] = calculate_work_experience(result[0]["date_of_joining"])
        return result[0]
    else:
        return {}

def calculate_work_experience(date_of_joining):
    delta = date_diff(getdate(), date_of_joining)
    # Convert the difference to years, months, and days
    years = delta // 365
    remaining_days = delta % 365
    months = remaining_days // 30
    days = remaining_days % 30
    return f"{years} year(s) {months} month(s) {days} day(s)"

def get_employee_history(filters):
    result = frappe.db.sql("""
        SELECT
            idx as serial_number,
            COALESCE(NULLIF(history.custom_description, ''), '-') as description,
            COALESCE(NULLIF(history.from_date, ''), '-') as effective_date,
            COALESCE(NULLIF(history.designation, ''), '-') as designation,
            (case when ifnull(history.custom_probation, 0)=0 then "-" else CONCAT('Rs ', FORMAT(history.custom_probation, 0)) end) as probation,
            (case when ifnull(history.custom_annual, 0)=0 then "-" else CONCAT('Rs ', FORMAT(history.custom_annual, 0)) end) as annual,
            (case when ifnull(history.custom_promotion, 0)=0 then "-" else CONCAT('Rs ', FORMAT(history.custom_promotion, 0)) end) as promotion,
            (case when ifnull(history.custom_special, 0)=0 then "-" else CONCAT('Rs ', FORMAT(history.custom_special, 0)) end) as special,
            (case when ifnull(history.custom_self_devp_copy, 0)=0 then "-" else CONCAT('Rs ', FORMAT(history.custom_self_devp_copy, 0)) end) as self_devp,
            (case when ifnull(history.custom_disparity_c, 0)=0 then "-" else CONCAT('Rs ', FORMAT(history.custom_disparity_c, 0)) end) as disparity,
            (case when ifnull(history.custom_salary_slab_adjustment_c, 0)=0 then "-" else CONCAT('Rs ', FORMAT(history.custom_salary_slab_adjustment_c, 0)) end) as salary_slab_adjustment,
            (case when ifnull(history.custom_confirmation_cy, 0)=0 then "-" else CONCAT('Rs ', FORMAT(history.custom_confirmation_cy, 0)) end) as confirmation,
            (case when ifnull(history.custom_salary, 0)=0 then "-" else CONCAT('Rs ', FORMAT(history.custom_salary, 0)) end) as salary
            -- ifnull(history.custom_probation, 0) as probation,
            -- ifnull(history.custom_annual, 0) as annual,
            -- ifnull(history.custom_promotion, 0) as promotion,
            -- ifnull(history.custom_special, 0) as special,
            -- ifnull(history.custom_self_devp_copy, 0) as self_devp,
            -- ifnull(history.custom_disparity_c, 0) as disparity,
            -- ifnull(history.custom_salary_slab_adjustment_c, 0) as salary_slab_adjustment,
            -- ifnull(history.custom_confirmation_c, 0) as confirmation,
            -- ifnull(history.custom_salary, 0) as salary
        FROM
            `tabEmployee Internal Work History` history
        WHERE
            history.parent = %(employee)s
        Order By
            serial_number
    """, {"employee": filters.get('employee')}, as_dict=1)
    i = 0
    for d in result:
        result[i]['effective_date'] = formatdate(result[i]['effective_date'])
        # result[i]['probation'] = fmt_money(result[i]['probation'], precision=0, currency="PKR") if(result[i]['probation']!="-") else "-"
        # result[i]['annual'] = fmt_money(result[i]['annual'], precision=0, currency="PKR") if(result[i]['annual']!="-") else "-"
        # result[i]['promotion'] = fmt_money(result[i]['promotion'], precision=0, currency="PKR") if(result[i]['promotion']!="-") else "-"
        # result[i]['special'] = fmt_money(result[i]['special'], precision=0, currency="PKR") if(result[i]['special']!="-") else "-"
        # result[i]['salary'] = fmt_money(result[i]['salary'], precision=0, currency="PKR") if(result[i]['salary']!="-") else "-"
        i = i + 1
    return result

@frappe.whitelist()
def set_print_content(content):
    frappe.db.set_value('Print Format', 'Employment History Report', 'html', content)
    return "Content successfully set for printing"
