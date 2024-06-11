import frappe, ast

@frappe.whitelist()
def fetch_counts(filters):
    filters = ast.literal_eval(filters)

    return {
        "total_head_count": get_head_count(filters),
        "total_present": get_present(filters),
        "total_absent": get_absent(filters)
    }

def get_conditions(filters): pass

def get_head_count(filters):
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

def get_present(filters):
    query = """ Select count(name)
        From `tabAttendance`
        Where docstatus=1
        and status in ("Present")"""
    query += " and company = %(company)s " if(filters.get("company")) else ""
    query += " and custom_branch = %(branch)s " if(filters.get("branch")) else ""
    query += "and attendance_date between %(from_date)s and %(to_date)s " if(filters.get('from_date') and filters.get('to_date')) else ""
    r = frappe.db.sql(query, filters)
    return r[0][0] if(r) else 0
    
def get_absent(filters):
    query = """ Select count(name)
        From `tabAttendance`
        Where docstatus=1
        and status in ("Present")"""
    query += " and company = %(company)s " if(filters.get("company")) else ""
    query += " and custom_branch = %(branch)s " if(filters.get("branch")) else ""
    query += "and attendance_date between %(from_date)s and %(to_date)s " if(filters.get('from_date') and filters.get('to_date')) else ""
    r = frappe.db.sql(query, filters)
    return r[0][0] if(r) else 0