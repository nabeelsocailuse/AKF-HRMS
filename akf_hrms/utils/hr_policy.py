""" 
1. Late comings will be considered, if not authorized, for arrival after starting time to two hours. 
    One casual leave, if that is not available in credit then one medical leave, 
    if that is not available in credit then one earned leave, 
    if that is also not available in credit then one day salary will be deducted of an employee for every three late comings in a month.

2. Similarly, for every two to less than four hours un-authorized late arrival on any day of a month will result in to deduction of half casual leave, 
    if that is not available in credit then half medical leave, 
    if that is not available in credit then half earned leave, 
    if that is also not available in credit then half day salary.

3. For every four hours or more un-authorized late arrival on any day of a month will result in to deduction of one casual leave, 
    if that is not available in credit then one medical leave, 
    if that is not available in credit then one earned leave, 
    if that is also not available in credit then one day salary.

4. For every un-authorized early departure of four hours or less on any day of a month will result in to deduction of half day salary.

5. The employee will be considered as absent if he/she does not mark his ‘In’ or ‘Out’ or both attendance on attendance machine. 
    Deduction of full day will be made in such cases. 
    However, special approval from the HoD may be entertained if he confirms that the employee was present in the office.

6. Any employee can adjust his late sittings in office/ In-station duties against upcoming late arrivals within a week. Late sitting should be
"""
import frappe

@frappe.whitelist(allow_guest=True)
def apply_policy(doc, method=None):
    args = frappe._dict({
        'company': doc.company,
        'employee': doc.employee,
        'posting_date': doc.attendance_date
    })
    two_hours_three_late_comings_times_in_a_month(args)
    above_two_and_less_four_hours_in_months(args)
    late_entry_above_four_hours_in_months(args)
    four_hours_or_less_early_exists_in_a_month(args)
    
# 1
@frappe.whitelist()
def two_hours_three_late_comings_times_in_a_month(args):
    result = frappe.db.sql(""" 
        select 
            count(TIME_TO_SEC(TIMEDIFF(cast(in_time as time), custom_start_time))/3600) hours
        from 
            `tabAttendance` 
        where 
            docstatus=1 
            and status='Present' 
            and ifnull(shift,"")!=""
            and ifnull(in_time,"")!="" 
            and late_entry=1 
            and company=%(company)s
            and employee=%(employee)s
            and month(attendance_date)=month(%(posting_date)s)
            and ((TIME_TO_SEC(TIMEDIFF(cast(in_time as time), custom_start_time))/3600)>0 and (TIME_TO_SEC(TIMEDIFF(cast(in_time as time), custom_start_time))/3600)<=2)
        having
            hours>0.0
    """, args)
    if(result):
        hours = result[0][0]
        if(hours%3==0):
            args.update({"reason": "Consective two hours late 3 times in a month."})
            verify_case_no(args, 1)

# 2
@frappe.whitelist()
def above_two_and_less_four_hours_in_months(args):

    result = frappe.db.sql(""" 
        select
            count(TIME_TO_SEC(TIMEDIFF(cast(in_time as time), custom_start_time))/3600) hours
        from 
            `tabAttendance` 
        where 
            docstatus=1 
            and status='Present' 
            and ifnull(shift,"")!="" 
            and ifnull(in_time,"")!="" 
            and late_entry=1 
            and company=%(company)s
            and employee=%(employee)s 
            and attendance_date=%(posting_date)s
            and ((TIME_TO_SEC(TIMEDIFF(cast(in_time as time), custom_start_time))/3600)>2 
                and (TIME_TO_SEC(TIMEDIFF(cast(in_time as time), custom_start_time))/3600)<4)
        having 
            hours>0
    """, args)

    if(result): 
        args.update({"reason": "Above two and less than 4 hours late in a month."})
        verify_case_no(args, 2)

# 3
@frappe.whitelist()
def late_entry_above_four_hours_in_months(args):
    result = frappe.db.sql(""" 
        select 
            count(TIME_TO_SEC(TIMEDIFF(cast(in_time as time), custom_start_time))/3600) hours
        from 
            `tabAttendance` 
        where 
            docstatus=1 
            and status='Present' 
            and ifnull(shift,"")!="" 
            and ifnull(in_time,"")!="" 
            and late_entry=1 
            and company=%(company)s
            and employee=%(employee)s
            and attendance_date=%(posting_date)s
            and (TIME_TO_SEC(TIMEDIFF(cast(in_time as time), custom_start_time))/3600)>=4
    """, args)

    if(result): 
        args.update({"reason": "Above or equal to 4 hours late in a month."})
        verify_case_no(args, 3)

# 4
def four_hours_or_less_early_exists_in_a_month(args):

    result = frappe.db.sql(""" 
        select 
            count(TIME_TO_SEC(TIMEDIFF(custom_end_time, cast(out_time as time)))/3600) hours
        from 
            `tabAttendance` 
        where 
            docstatus=1 
            and status='Present' 
            and ifnull(shift,"")!=""
            and ifnull(out_time,"")!=""
            and early_exit=1 
            and company=%(company)s
            and employee=%(employee)s
            and attendance_date=%(posting_date)s
            and ((TIME_TO_SEC(TIMEDIFF(custom_end_time, cast(out_time as time)))/3600)>0 
                and (TIME_TO_SEC(TIMEDIFF(custom_end_time, cast(out_time as time)))/3600)<=4)
        having
            hours>0
    """, args)
    
    if(result): 
        args.update({"reason": "Early exit four hours or less late in a month."})
        verify_case_no(args, 4)

# 5
def absent_if_in_or_out_missed_or_both():
    pass

""" 

Deduction Leave Applicaion.
        Or
Additinal Salary in case of no leaves left.

"""

@frappe.whitelist()
def verify_case_no(args, case_no=0):
    args = get_balance(args)

    if(case_no == 1):
        if(args.deduction_type == "Salary"):
            args.update({
                'reason': f"CaseNo#{case_no}, {args.reason} One day salary deducted.",
            })
        elif(args.deduction_type == "Leave"):
            args.update({
                'total_deduction': 1,
                'reason': f"CaseNo#{case_no}, {args.reason} '{args.leave_type}' deducted.",
            })
        print(f"args: {args}")
    elif(case_no == 2):
        if(args.deduction_type == "Salary"):
            args.update({
                'total_deduction': args.total_deduction/2,
                'reason': f"CaseNo#{case_no}, {args.reason} Half day salary deducted.",
            })
        elif(args.deduction_type == "Leave"):
            args.update({
                'total_deduction': 0.5,
                'reason': f"CaseNo#{case_no}, {args.reason}. Half '{args.leave_type}' deducted.",
            })
        print(f"args: {args}")
    elif(case_no == 3):
        if(args.deduction_type == "Salary"):
            args.update({
                'total_deduction': args.total_deduction,
                'reason': f"CaseNo#{case_no}, {args.reason} One day salary deducted.",
            })
        elif(args.deduction_type == "Leave"):
            args.update({
                'total_deduction': 1,
                'reason': f"CaseNo#{case_no}, {args.reason}. '{args.leave_type}' deducted.",
            })
        print(f"args: {args}")
    elif(case_no == 4):
        args.update({
                'leave_type': None,
                'deduction_type': 'Salary',
                'total_deduction': args.total_deduction/2,
                'reason': f"CaseNo#{case_no}, {args.reason} Half day salary deducted.",
            })
        print(f"args: {args}")
    elif(case_no == 5):
        pass

    # create new entry
    if(args.total_deduction>0.0): create_deduction_ledger_entry(args)

def get_balance(args):
    from akf_hrms.overrides.leave_application import get_leave_details

    leave_balance = get_leave_details(args.employee, args.posting_date)
    leave_allocation = leave_balance['leave_allocation']
    
    remaining_leaves = 0.0
    leave_type = None
    deduction_type = None

    for key in leave_allocation:
        leave_type = key

        if(key == 'Casual Leave'):
            remaining_leaves = leave_allocation[key]['remaining_leaves']
        elif(key == 'Medical leave'):
            remaining_leaves = leave_allocation[key]['remaining_leaves']
        elif(key == 'Earned leave'):
            remaining_leaves = leave_allocation[key]['remaining_leaves']

        if(remaining_leaves>0.0): 
            deduction_type = 'Leave'
            break
        else: 
            leave_type = None
            deduction_type = 'Salary'

    return args.update({
        "deduction_type":  deduction_type,
        "leave_type": leave_type,
        "total_deduction": get_wage(args)
    })

def get_wage(args):
    r = frappe.db.sql(""" 
        select ifnull((base/30),0) as wages
        from `tabSalary Structure Assignment`
        where 
            docstatus=1
            and company= %(company)s
            and employee= %(employee)s
        having
            wages>0
        order by
            from_date desc
    """, args)
    return r[0][0] if(r) else 0  

def create_deduction_ledger_entry(args):
    args.update({"doctype": 'Deduction Ledger Entry'})
    filters = args.copy()
    filters.pop("deduction_type")
    filters.pop("leave_type")
    filters.pop("total_deduction")
    if(not frappe.db.exists(filters)): frappe.get_doc(args).insert(ignore_permissions=True)

