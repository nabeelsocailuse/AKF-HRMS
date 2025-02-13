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
import frappe, math
from frappe.utils import (flt, month_diff, add_months, getdate, get_datetime, add_to_date, get_first_day, get_last_day, date_diff)
from datetime import datetime, timedelta
from dateutil import relativedelta

@frappe.whitelist(allow_guest=True)
def apply_policy(doc, method=None):
    args = frappe._dict({
        'company': doc.company,
        'employee': doc.employee,
        'posting_date': doc.attendance_date,
        'transition_type': 'Attendance',
        'transition_name': doc.attendance_id,
        
    })
    out_time = frappe.db.get_value('Attendance', doc.attendance_id, 'out_time') if(doc.attendance_id) else None
    if(not out_time):
        two_hours_three_late_comings_times_in_a_month(args)
        above_two_and_less_four_hours_in_months(args)
        late_entry_above_four_hours_in_months(args)
    elif(out_time):
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
            hours>0
    """, args)
    if(result):
        hours = result[0][0]
        if(hours%3==0):
            total_iterations = (hours/3)
            args.update({
                'case_no': 1,
                "reason": "Consective two hours late 3 times in a month.",
            })
            returnVal = validate_case_no_in_DLE(args)
            if(total_iterations>returnVal):
                verify_case_no(args)

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
        
        args.update({
            'case_no': 2,
            "reason": "Above two and less than 4 hours late in a month.",
            })
        actualVal = result[0][0]
        returnVal = validate_case_no_in_DLE(args)
        if(actualVal>returnVal):
            verify_case_no(args)

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
        having 
            hours>0
    """, args)
    print(f'---------------late_entry_above_four_hours_in_months: {result}')
    if(result): 
        args.update({
            'case_no': 3,
            "reason": "Above or equal to 4 hours late in a month.",
            })
        actualVal = result[0][0]
        returnVal = validate_case_no_in_DLE(args)
        if(actualVal>returnVal):
            verify_case_no(args)

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
        args.update({
            'case_no': 4,
            "reason": "Early exit four hours or less late in a month.",
            })
        actualVal = result[0][0]
        returnVal = validate_case_no_in_DLE(args)
        if(actualVal>returnVal):
            verify_case_no(args)

# 5
def absent_if_in_or_out_missed_or_both():
    pass

def validate_case_no_in_DLE(args):
    
    conditions =  """ and month(posting_date)=month(%(posting_date)s)""" if(args.case_no==1) else ""
    conditions +=  """ and posting_date=%(posting_date)s""" if(args.case_no==2) else ""
    conditions +=  """ and posting_date=%(posting_date)s""" if(args.case_no==3) else ""
    conditions +=  """ and posting_date=%(posting_date)s""" if(args.case_no==4) else ""
    res =  frappe.db.sql("""select count(name) from `tabDeduction Ledger Entry` 
                where 
                company=%(company)s
                and employee=%(employee)s
                and case_no = %(case_no)s 
                {0}
                """.format(conditions), args)
    
    if(res):
        return res[0][0]
    return 0     

""" Deduction Leave Applicaion.
    Or
Additinal Salary in case of no leaves left.
"""

@frappe.whitelist()
def verify_case_no(args):
    args = get_balance(args)
    
    case_no  = args.case_no
    if(case_no == 1):
        if(args.deduction_type == "Salary"):
            args.update({
                'total_deduction': 1,
                'reason': f"CaseNo#{case_no}, {args.reason} One day salary deducted.",
            })
        elif(args.deduction_type == "Leave"):
            args.update({
                'total_deduction': 1,
                'reason': f"CaseNo#{case_no}, {args.reason} '{args.leave_type}' deducted.",
            })
    elif(case_no == 2):
        if(args.deduction_type == "Salary"):
            args.update({
                'total_deduction': 0.5,
                'reason': f"CaseNo#{case_no}, {args.reason} Half day salary deducted.",
            })
        elif(args.deduction_type == "Leave"):
            args.update({
                'total_deduction': 0.5,
                'reason': f"CaseNo#{case_no}, {args.reason}. Half '{args.leave_type}' deducted.",
            })
    elif(case_no == 3):
        if(args.deduction_type == "Salary"):
            args.update({
                'total_deduction': 1,
                'reason': f"CaseNo#{case_no}, {args.reason} One day salary deducted.",
            })
        elif(args.deduction_type == "Leave"):
            args.update({
                'total_deduction': 1,
                'reason': f"CaseNo#{case_no}, {args.reason}. '{args.leave_type}' deducted.",
            })
    elif(case_no == 4):
        args.update({
                'deduction_type': 'Salary',
                'leave_type': 'Leave Without Pay',
                'total_deduction': 0.5,
                'reason': f"CaseNo#{case_no}, {args.reason} Half day salary deducted.",
            })
    elif(case_no == 5):
        pass

    # create new entry
    if(args.total_deduction>0.0): make_attendance_deduction_ledger_entry(args)

def get_balance(args):
    from akf_hrms.overrides.leave_application.leave_application import get_leave_details

    leave_balance = get_leave_details(args.employee, args.posting_date)
    leave_allocation = leave_balance['leave_allocation']
    
    remaining_leaves = 0.0
    leave_type = None
    deduction_type = None

    isBal = False
    if('Casual Leave' in leave_allocation):
        leave_type = 'Casual Leave'
        remaining_leaves = leave_allocation[leave_type]['remaining_leaves']
        if(remaining_leaves>0.0): isBal = True
        
    if('Medical Leave' in leave_allocation) and (not isBal):
        leave_type = 'Medical Leave'
        remaining_leaves = leave_allocation[leave_type]['remaining_leaves']
        if(remaining_leaves>0.0): isBal = True
    
    if('Earned Leave' in leave_allocation) and (not isBal):
        leave_type = 'Earned Leave'
        remaining_leaves = leave_allocation[leave_type]['remaining_leaves']
        if(remaining_leaves>0.0): isBal = True
    
    if((not isBal)):
        leave_type = "Leave Without Pay"
        
    deduction_type = 'Leave' if(remaining_leaves>0.0) else 'Salary'
    
    return args.update({
        "deduction_type":  deduction_type,
        "leave_type": leave_type,
        # "total_deduction": get_wage(args)
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

def make_attendance_deduction_ledger_entry(args):
    args.update({"doctype": 'Deduction Ledger Entry'})
    # filters = args.copy()
    # filters.pop("transition_type")
    # filters.pop("transition_name")
    # filters.pop("deduction_type")
    # filters.pop("leave_type")
    # filters.pop("total_deduction")
    # filters.pop("reason")
    # frappe.throw(f"{filters}")
    # if(not frappe.db.exists(filters)): 
    frappe.get_doc(args).insert(ignore_permissions=True)

@frappe.whitelist()
def get_deduction_ledger(self=None):
    from akf_hrms.overrides.leave_application.leave_application import get_leave_details
    leave_allocation = get_leave_details(self.employee, self.start_date)
    
    pre_start_date = add_to_date(self.start_date, days=-30)
    pre_start_date = getdate(get_datetime(pre_start_date).replace(day=21))
    pre_end_date = add_to_date(self.end_date, days=-30)
    pre_end_date = getdate(get_datetime(pre_end_date).replace(day=20))
    
    result = frappe.db.sql(f""" 
        Select  ifnull(sum(total_deduction),0) as total,
                leave_type
        From
            `tabDeduction Ledger Entry`
        Where
            ifnull(leave_type, "")!=""
            and employee='{self.employee}'
            and (posting_date between '{pre_start_date}' and '{pre_end_date}')
        Group By
            leave_type
    """, as_dict=1)
    
    leave_balance = leave_allocation['leave_allocation']
    rcl = leave_balance["Casual Leave"]['remaining_leaves'] if("Casual Leave" in leave_balance) else 0
    rml = leave_balance["Medical Leave"]['remaining_leaves'] if("Medical Leave" in leave_balance) else 0
    rel = leave_balance["Earned Leave"]['remaining_leaves'] if("Earned Leave" in leave_balance) else 0
    rlwp = leave_balance["Leave Without Pay"]['remaining_leaves'] if("Leave Without Pay" in leave_balance) else 0
    
    def get_actual_deductions(balance, actual_balance):
        if(balance>0):
            if(actual_balance<=balance):
                return {
                    'cutbal': actual_balance,
                    'forwordbal': 0
                }
            else: 
                forwordbal = (actual_balance - balance) # leftbalance = 5 - 2  = 3
                cutbal =  (actual_balance - forwordbal) # remain = 5 - 3  = 2
                return {
                        'cutbal': cutbal,
                        'forwordbal': forwordbal
                    }
        else:
            return {
                'cutbal': 0,
                'forwordbal': actual_balance
            }
    
    scl = sml = sel = slwp = 0
    for d in result:
        actual_balance = d.total
        if(d.leave_type=="Casual Leave"):
            rdict = get_actual_deductions(rcl, actual_balance)
            rcl = rcl - rdict['cutbal']
            scl += rdict['cutbal']
            forwordbal = rdict['forwordbal']
            
            if(forwordbal>0):
                rdict = get_actual_deductions(rml, forwordbal)
                rml = rml - rdict['cutbal']
                sml += rdict['cutbal']
                forwordbal = rdict['forwordbal']
                
                if(forwordbal>0):
                    rdict = get_actual_deductions(rel, forwordbal)
                    rel = rel - rdict['cutbal']
                    sel += rdict['cutbal']
                    forwordbal = rdict['forwordbal']
                    
                    if(forwordbal>0):
                        slwp += forwordbal
                        
        elif(d.leave_type=="Medical Leave"):
            rdict = get_actual_deductions(rml, actual_balance)
            rml = rml - rdict['cutbal']
            sml += rdict['cutbal']
            forwordbal = rdict['forwordbal']
            
            if(forwordbal>0):
                rdict = get_actual_deductions(rel, forwordbal)
                rel = rel - rdict['cutbal']
                sel += rdict['cutbal']
                forwordbal = rdict['forwordbal']
                
                if(forwordbal>0):
                    rdict = get_actual_deductions(rcl, forwordbal)
                    rcl = rcl - rdict['cutbal']
                    scl += rdict['cutbal']
                    forwordbal = rdict['forwordbal']
                    
                    if(forwordbal>0):
                        slwp += forwordbal
                        
        elif(d.leave_type=="Earned Leave"):
            rdict = get_actual_deductions(rel, rdict['forwordbal'])
            rel = rel - rdict['cutbal']
            sel += rdict['cutbal']
            forwordbal = rdict['forwordbal']
            if(forwordbal>0):
                rdict = get_actual_deductions(rml, forwordbal)
                rml = rml - rdict['cutbal']
                sml += rdict['cutbal']
                forwordbal = rdict['forwordbal']
                if(forwordbal>0):
                    rdict = get_actual_deductions(rcl, forwordbal)
                    rcl = rcl - rdict['cutbal']
                    scl += rdict['cutbal']
                    forwordbal = rdict['forwordbal']
                    if(forwordbal>0):
                        slwp += forwordbal
                
        elif(d.leave_type=="Leave Without Pay"):
            slwp += actual_balance
    
    self.custom_deduction_start_date = pre_start_date
    self.custom_deduction_end_date = pre_end_date
    self.custom_casual_leaves =  scl
    self.custom_medical_leaves = sml
    self.custom_earned_leaves = sel
    self.custom_leaves_without_pay = (slwp+rlwp)

""" SALARY SLIP POLICIES """

def validate_other_info(self=None):
    self.custom_pf_eligibility = self.start_date
    employment_type = frappe.get_value("Employee", self.employee, "employment_type")
    date_of_joining = frappe.get_value("Employee", self.employee, "date_of_joining")
    if employment_type == "Regular":
        # if get_datetime(date_of_joining) < get_datetime(add_months(self.start_date, -6)):
        if month_diff(self.start_date, date_of_joining)>6:
            self.custom_pf_deduction = "Yes"
            self.custom_pf_start_month = add_months(date_of_joining, 6)
            pf_list = []
            for d in self.deductions:
                pf_list.append(d.salary_component)
            
            if ("Provident Fund" not in pf_list) and (self.pf_employer_contribution>0):
                self.append("deductions",{
                    "salary_component":"Provident Fund",
                    "amount": self.pf_employer_contribution
                })
                self.total_deduction = self.total_deduction + self.pf_employer_contribution
        else:
            self.custom_pf_deduction = "No"
            self.pf_employer_contribution = 0
    else:
        self.pf_employer_contribution = 0
    
    if get_datetime(date_of_joining) < get_datetime(add_months(self.start_date, -6)):
        if get_datetime(date_of_joining) < get_datetime(add_months(self.start_date, -12)):
            self.custom_summer_break = "Paid as Usual"
        else:
            self.custom_summer_break = "Hold"
    else:
        self.custom_summer_break = "N/A"

    d1 = str(self.start_date).split("-")
    d2 = str(date_of_joining).split("-")
    date1 = datetime(int(d1[0]), int(d1[1]), int(d1[2]))
    date2 = datetime(int(d2[0]), int(d2[1]), int(d2[2]))

    diff = relativedelta.relativedelta(date1, date2)

    years_ = diff.years
    months_ = diff.months
    days_ = diff.days

    self.custom_summer_break_eligibility = '{} years, {} months, {} days'.format(years_, months_, days_)
    self.custom_service_duration_for_6_months_pf_eligibility = '{} years, {} months, {} days'.format(years_, months_, days_)

@frappe.whitelist()
def get_eobi_pf_social_security_details(self=None):      
    # Validate EOBI Employer Contribution
    employee = frappe.get_doc("Employee", {"name": self.employee}, ["name", "custom_eobi_applicable"])
    if employee.custom_eobi_applicable == 1:
        self.custom_eobi_employer_contribution = frappe.db.get_value("AKF Payroll Settings", None, "eobi_employer_contribution")   
        # Validate EOBI Employee Contribution
        eobi_employee_contribution = frappe.db.get_value("AKF Payroll Settings", None, "eobi_employee_contribution")
        for d in self.deductions:
            if d.salary_component == "EOBI":
                d.amount = eobi_employee_contribution
    # Validate Provident Employee/Employer Contribution
    date_of_joining = frappe.db.get_value("Employee", {"name": self.employee}, "date_of_joining")
    delay_of_provident_fund_deduction = frappe.db.get_value("AKF Payroll Settings", None, "delay_of_provident_fund_deduction")
    delay_months = 30*int(delay_of_provident_fund_deduction)
    if date_of_joining:
        delay_limit = datetime.now().date() - timedelta(days=delay_months)
        if date_of_joining < delay_limit:
            pf_employer_contribution_percent = frappe.db.get_value("AKF Payroll Settings", None, "provident_employer_contribution_percent")
            pf_employer_contribution_percent = float(pf_employer_contribution_percent if pf_employer_contribution_percent is not None else 0)
            self.custom_provident_fund_employer_contribution = (float(self.gross_pay or 0.0) * pf_employer_contribution_percent)/100.0
            
            pf_employee_contribution_percent = frappe.db.get_value("AKF Payroll Settings", None, "provident_employee_contribution_percent")
            provident_fund_employee_contribution = (float(self.gross_pay or 0.0) * float(pf_employee_contribution_percent))/100.0
            for d in self.deductions:
                if d.salary_component == "Provident Fund":
                    d.amount = provident_fund_employee_contribution

    # Validate Social Security
    social_security_amount = frappe.db.get_value("AKF Payroll Settings", None, "social_security_amount")
    social_security_rate = frappe.db.get_value("AKF Payroll Settings", None, "social_security_rate")		
    
    if flt(self.gross_pay) <= flt(social_security_amount):                     
        ssa_gross_pay = frappe.db.get_value("Salary Structure Assignment", {"employee": self.employee, "docstatus":1}, "base")                  
        social_security_amount_deduction = flt(ssa_gross_pay) * flt(social_security_rate) 
        for d in self.deductions:
            if d.salary_component == "Social Security":
                d.amount = social_security_amount_deduction
    get_set_takful_plan(self)
        
@frappe.whitelist()
def get_set_takful_plan(self=None):
    # Validate Takaful Plan Employee/Employer Contribution
    employee = frappe.get_doc("Employee", {"name": self.employee}, ["name", "custom_takaful_plan"])
    if employee.custom_takaful_plan:
        # frappe.msgprint(frappe.as_json(employee))
        tk_plan = frappe.get_doc("Takaful Plan", {"name": employee.custom_takaful_plan}, ["employer_contribution", "employee_contibution"])
        self.custom_takaful_plan_employer_contribution = tk_plan.employer_contribution
        for d in self.deductions:
            if d.salary_component == "Takaful Plan":
                d.amount = tk_plan.employee_contribution


""" 
args = dict(
    leaves=self.total_leave_days * -1,
    from_date=self.from_date,
    to_date=self.to_date,
    is_lwp=lwp,
    holiday_list=get_holiday_list_for_employee(self.employee, raise_exception=raise_exception)
    or "",
)
create_leave_ledger_entry(self, args, submit)
"""             
def make_leave_ledger_entry(self=None):
    # def create_leave_application(leave_type, leaves, reason):
    #     from erpnext.setup.doctype.employee.employee import get_holiday_list_for_employee
    #     from akf_hrms.overrides.leave_application import get_leave_approver
        
    #     # dates logic
    #     days = math.ceil(leaves)
    #     from_date = add_to_date(self.start_date)
    #     to_date = add_to_date(self.start_date, days=(days-1))
    #     # frappe.throw(f" {leave_type}:  {days} {from_date} {to_date}")
    #     if(leave_type == "Leave Without Pay"):
    #         from_date = add_months(self.start_date, months=1)
    #         to_date = add_to_date(from_date, days=(days-1))
        
    #     # setup half day logic
    #     fractional_part, integer_part = math.modf(leaves)
        
    #     half_day = 0
    #     half_day_date = None
    #     if(fractional_part>0.0 and integer_part>0.0):
    #         half_day = 1
    #         half_day_date = to_date
            
    #     elif(fractional_part>0.0 and integer_part==0.0):
    #         half_day = 1
            
    #     args = frappe._dict({
    #         'doctype': 'Leave Application',
    #         'employee': self.employee,
    #         'leave_type': leave_type,
    #         'company': self.company,
    #         'from_date': from_date,
    #         'to_date': to_date,
    #         'half_day': half_day,
    #         'half_day_date': half_day_date,
    #         'total_leave_days':  leaves,
    #         'leave_approver': get_leave_approver(self.employee),
    #         'follow_via_email': 0,
    #         'salary_slip': self.name,
    #         'reason': reason,
    #         'status': 'Approved'
    #     })
    #     doc = frappe.get_doc(args)
    #     doc.flags.ignore_permissions=1
    #     doc.flags.ignore_validate=1
    #     doc.submit()
    if(not self.custom_apply_deductions): return 
    def _create_(leave_type, leaves):
        from erpnext.setup.doctype.employee.employee import get_holiday_list_for_employee
        from akf_hrms.overrides.leave_application import get_leave_approver
        days = math.ceil(leaves)
        from_date = add_to_date(self.start_date)
        to_date = add_to_date(self.start_date, days=(days-1))
        """ if(leave_type == "Leave Without Pay"):
            from_date = add_months(self.start_date, months=1)
            to_date = add_to_date(from_date, days=(days-1)) """
            
        doc = frappe.get_doc({
            'doctype': 'Leave Ledger Entry',
            'employee': self.employee,
            'leave_type': leave_type,
            'transaction_type': 'Salary Slip',
            'transaction_name': self.name,
            'company': self.company,
            'leaves': (-1 * leaves),
            'from_date': from_date,
            'to_date': to_date,
            "holiday_list": get_holiday_list_for_employee(self.employee, raise_exception=False)
        })
        # frappe.throw(frappe.as_json(doc))
        doc.flags.ignore_permissions=1
        doc.submit()
        
    # casual leave
    leave_type = None
    if(self.custom_casual_leaves>0.0):
        leave_type = 'Casual Leave'
        # create_leave_application(leave_type, self.custom_casual_leaves, f'{leave_type}: {self.custom_casual_leaves}, deducted through Salary Slip.')
        _create_(leave_type, self.custom_casual_leaves)
        # create_dlle('Casual Leave', self.custom_casual_leaves)
    # medical leave
    if(self.custom_medical_leaves>0.0):
        leave_type = 'Medical Leave'
        # create_leave_application(leave_type, self.custom_medical_leaves, f'{leave_type}: {self.custom_medical_leaves}, deducted through Salary Slip.')
        _create_(leave_type, self.custom_medical_leaves)
        # create_dlle('Medical Leave', self.custom_medical_leaves)
    # earned leave
    if(self.custom_earned_leaves>0.0):
        leave_type = 'Earned Leave'
        # create_leave_application(leave_type, self.custom_earned_leaves, f'{leave_type}: {self.custom_earned_leaves}, deducted through Salary Slip.')
        _create_(leave_type, self.custom_earned_leaves)
        # create_dlle('Earned Leave', self.custom_earned_leaves)
    # lwp
    if(self.custom_leaves_without_pay>0.0): 
        leave_type = 'Leave Without Pay'
        # create_leave_application(leave_type, self.custom_leaves_without_pay, f'{leave_type}: {self.custom_leaves_without_pay}, deducted through Salary Slip.')
        # _create_(leave_type, self.custom_leaves_without_pay)
        # create_dlle('Leave Without Pay', self.custom_leaves_without_pay)

def cancel_leave_ledger_entry(self=None):
    # cancel_leave_application(self)
    if(frappe.db.exists('Leave Ledger Entry', {'transaction_name': self.name})):
        frappe.db.sql(f""" 
            delete from `tabLeave Ledger Entry`
            where  transaction_name = '{self.name}'  
        """)
       
def cancel_leave_application(self=None):
    for d in frappe.db.get_list('Leave Application', 
        filters={'docstatus': 1, 'employee': self.employee, 'salary_slip': self.name}, 
        fields=['name']):
        
        frappe.db.sql(f""" 
            delete from `tabLeave Ledger Entry`
            where transaction_name = '{d.name}'  
        """)
        
        frappe.db.sql(f""" 
            delete from `tabLeave Application`
            where name = '{d.name}'  
        """)
       
@frappe.whitelist()
def get_no_attendance(self=None):
    if (frappe.db.exists('Employee', {'status': 'Active', 'name': self.employee, 'custom_no_attendance': 1})):
        return True
    return False

def get_leave_without_pay_count(self=None):
    lwp = frappe.db.sql(f""" select ifnull(sum(leaves), 0) lwp 
                            from `tabLeave Ledger Entry`
                            where docstatus=1
                            and leave_type = 'Leave Without Pay'
                            and transaction_type = 'Salary Slip'
                            and employee = '{self.employee}'
                            and  from_date>='{self.start_date}' and to_date<='{self.end_date}' """)
    # and to_date<='{self.end_date}'
    # frappe.throw(f"{lwp}")
    if(lwp): 
        return (-1 * lwp[0][0])
    return 0

""" 
    > Salary Period: [21-Nov, 20-Dec]. 
    > If salary disburse at 20-Dec. 
    > But new employee joins at 21-Dec pay his arrears through Additional Salary. 
"""
def record_employee_arrears_draft_additional_salary(self=None):
    
    def no_salary_slip():
        if(frappe.db.exists('Salary Slip', 
            {'docstatus': ['<', 2], 'employee': self.employee, 'company':self.company}
        )):
            return False
        return True
            
    def validate_date_of_joining():
        date_of_joining = getdate(self.date_of_joining)
        payroll_start_date = getdate(self.date_of_joining).replace(day=21)
        
        if(date_of_joining>=payroll_start_date):
            create_additional_salary()
        else:
            remove_additional_salary()
    
    def get_args(): 
        return {
            'employee': self.employee,
            'docstatus': 0,
            'salary_component': "Arrears",
            'company': self.company,
            'overwrite_salary_structure_amount': 0,
        }
    
    def get_no_of_days():
        return date_diff(get_last_day(self.date_of_joining), self.date_of_joining) + 1
    
    def create_additional_salary():
        payroll_date = get_first_day(add_to_date(self.date_of_joining, months=1))
        args = get_args()
        name = frappe.db.get_value('Additional Salary', args, 'name')
        if(name):
            doc = frappe.get_doc('Additional Salary', name)
            doc.amount = get_no_of_days()
            doc.flags.ignore_permissions=1
            doc.save()
        else:
            args.update({
                'doctype': 'Additional Salary',
                'payroll_date': payroll_date,
                'amount': get_no_of_days(),
            })
            doc = frappe.get_doc(args)
            doc.flags.ignore_permissions=1
            doc.insert()
    
    def remove_additional_salary():
        args = get_args()
        name = frappe.db.get_value('Additional Salary', args, 'name')
        if(name):
            frappe.delete_doc('Additional Salary', name)
    
    if(self.status=='Active' and no_salary_slip()): 
        validate_date_of_joining()
        

def submit_employee_additional_salary_arrears(self=None):
    def get_args(): 
        return {
            'payroll_date': [">", self.from_date],
            'docstatus': 0,
            'employee': self.employee,
            'salary_component': "Arrears",
            'company': self.company,
            'overwrite_salary_structure_amount': 0,
        }
    args = get_args()
    for d in frappe.db.get_list('Additional Salary', filters=args, fields=["*"]):
        doc = frappe.get_doc('Additional Salary', d.name)
        doc.amount  = doc.amount * self.custom_per_day
        doc.flags.ignore_permissions
        doc.save()
        doc.submit()
        
        