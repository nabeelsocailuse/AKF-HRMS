import frappe

def execute():
    if not frappe.db.exists("Custom Field", "HR Settings-skip_validations_role"):
        frappe.get_doc({
            "doctype": "Custom Field",
            "dt": "HR Settings",  # Target DocType
            "module": "Akf Hrms",
            "label": "Skip Validations Role",  # Field label
            "fieldname": "skip_validations_role",  # Fieldname in code
            "fieldtype": "Link",  # Choose your field type (e.g., Data, Int, Check, etc.)
            "options": "Role",
            "insert_after": "exit_questionnaire_web_form",  # Insert after an existing field
            "description": "This is used to skip validations in any doctype."
        }).insert()

def skip():
    skip_validations_role = frappe.db.get_single_value("HR Settings", "skip_validations_role")
    if (skip_validations_role):
        if (skip_validations_role in frappe.get_roles(frappe.session.user)):
            return True
        return False
    return False
