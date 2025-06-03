import frappe


@frappe.whitelist(allow_guest=True)
def submit_on_complete(doc, method=None):
    """
    This function will be called when a new Employee onboarding or Employee Separation document is submitted.
    It will stop the user to not submit document if all activities are not completed.
    """
    for d in doc.activities:
        if not d.custom_completed:
            frappe.throw(
                f"Not allowed to Submit unless all the tasks are completed and 'Mark as Completed' is pressed"
            )
