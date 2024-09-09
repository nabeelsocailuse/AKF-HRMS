import frappe, json
from frappe.utils import formatdate, fmt_money

@frappe.whitelist()
def get_information(filters):
    filters = json.loads(filters)

    employee_detail = get_employee_details(filters)
    employee_history = get_employee_history(filters)
    hasEmployee = bool(employee_detail)

    data = {
        "hasEmployee": hasEmployee,
        "detail": employee_detail,
        "history": employee_history
    }

    return data

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
        return result[0]
    else:
        return {}

def get_employee_history(filters):
    result = frappe.db.sql("""
        SELECT
            idx as serial_number,
            COALESCE(NULLIF(history.custom_description, ''), '-') as description,
            COALESCE(NULLIF(history.from_date, ''), '-') as effective_date,
            COALESCE(NULLIF(history.designation, ''), '-') as designation,
            COALESCE(NULLIF(ROUND(history.custom_probation, 0), ''), '-') as probation,
            COALESCE(NULLIF(ROUND(history.custom_annual, 0), ''), '-') as annual,
            COALESCE(NULLIF(ROUND(history.custom_promotion, 0), ''), '-') as promotion,
            COALESCE(NULLIF(history.custom_special, ''), '-') as special,
            COALESCE(NULLIF(history.custom_self_devp, ''), '-') as self_devp,
            COALESCE(NULLIF(history.custom_disparity, ''), '-') as disparity,
            COALESCE(NULLIF(history.custom_salary_slab_adjustment, ''), '-') as salary_slab_adjustment,
            COALESCE(NULLIF(history.custom_confirmation, ''), '-') as confirmation,
            COALESCE(NULLIF(ROUND(history.custom_salary, 0), ''), '-') as salary
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
        result[i]['promotion'] = fmt_money(result[i]['promotion'], precision=0, currency="PKR")
        result[i]['special'] = fmt_money(result[i]['special'], precision=0, currency="PKR")
        result[i]['salary'] = fmt_money(result[i]['salary'], precision=0, currency="PKR")
        i = i + 1
    return result

@frappe.whitelist()
def set_print_content(content):
    frappe.db.set_value('Print Format', 'Employment History Report', 'html', content)
    return "Content successfully set for printing"
