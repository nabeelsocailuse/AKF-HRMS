import frappe

def execute():
    if (frappe.db.exists("Workspace", "Self Service Version-1")):
        if not frappe.db.exists("Custom HTML Block", "Self Service Dashboard"):
            frappe.get_doc({
                "doctype": "Custom HTML Block",
                "__newname": "Self Service Dashboard",
                "html": """ 
                        <div class="workspace-container">
                            <div class="employee-info">
                                <div class="employee-details">
                                <h2 id="employee-name"></h2>
                                <div class="profile-image">
                                    <img id="employee-image" src="" alt="Employee Image" />
                                </div>
                                <p>
                                    <span id="employee-name-value"></span>
                                    <strong>Department:</strong> 
                                    <span id="employee-department"></span>
                                </p>
                                <p>
                                    <strong>Branch:</strong> 
                                    <span id="employee-branch"></span>
                                    <strong>Designation:</strong> 
                                    <span id="employee-designation"></span>
                                </p>
                                </div>
                            </div>
                            <div class="leave-balance">
                                <h3>Leave Balance</h3>
                                <div class = "row" id="leave-balance-container">
                                
                                </div>
                            </div>
                        </div>
                """,  
                "script": """ let employeeInfoElement = root_element.querySelector('.employee-details');

                    function formatDate(dateString) {
                        if (!dateString) return '-'; 
                        const dateParts = dateString.split('-'); 
                        return `${dateParts[2]}-${dateParts[1]}-${dateParts[0]}`; 
                    }

                    frappe.call({
                        method: "akf_hrms.akf_hrms.doctype.expense_claim.expense_claim.get_employee_details",
                        callback: function(response) {
                            console.log("Response from employee details:", response);

                            if (response.message && response.message.message) {
                                employeeInfoElement.innerHTML = '<p>No records found!</p>'; 
                                return;
                            } 

                            if (response.message) {
                                let employee = response.message;
                                let employeeImageHTML = employee.image 
                                    ? `<div class="employee-image-container"><img id="employee-image" src="${employee.image}" alt="Employee Image" class="employee-image" /></div>`
                                    : `<div class="employee-image-container" style="width: 100px; height: 100px; border: 1px solid #ccc; display: flex; align-items: center; justify-content: center;"><p style="text-align: center; margin: 0;">No Image</p></div>`;
                                    
                                employeeInfoElement.innerHTML = `
                                    <div class="employee-content-img">${employeeImageHTML}</div>
                                    <div class="employee-content">
                                        <div class="employee-name"><strong>${employee.first_name || '-'}</strong></div>
                                        <div class="employee-content-list">
                                            <ul>
                                                <li><strong>Date of Joining:</strong> ${formatDate(employee.date_of_joining)}</li> <!-- Use the formatDate function here -->
                                                <li><strong>Branch:</strong> ${employee.branch || '-'}</li>
                                                <li><strong>Designation:</strong> ${employee.designation || '-'}</li>
                                            </ul>
                                            <ul>
                                                <li><strong>CNIC:</strong> ${employee.cnic || '-'}</li>
                                                <li><strong>Department:</strong> ${employee.department || '-'}</li>
                                                <li><strong>Employment Type:</strong> ${employee.employment_type || '-'}</li>
                                            </ul>
                                        </div>
                                    </div>
                                `;
                            }
                        },
                        error: function(error) {
                            console.error("Error fetching employee details", error);
                            employeeInfoElement.innerHTML = '<p>Unable to fetch employee details!</p>';
                        }
                    });

                    let globalEmployeeId;
                    let globalDate;

                    frappe.call({
                        method: "akf_hrms.akf_hrms.doctype.expense_claim.expense_claim.get_employee_date",
                        callback: function(response) {
                            console.log("GET EMPLOYEE AND DATE", response);

                            if (response.message) {
                                globalEmployeeId = response.message.name;  
                                globalDate = response.message.date;        

                                console.log("Employee ID:", globalEmployeeId);
                                console.log("Date:", globalDate);

                                if (globalEmployeeId == "undefined") {
                                    console.error("Employee ID is null or undefined. Cannot fetch leave details.");
                                    leaveBalanceElement.innerHTML = '<p>No leaves allocated!</p>'; 
                                } else {
                                    fetchLeaveDetails(globalEmployeeId, globalDate);
                                }
                            } else {
                                console.error("No employee found for the user or an unexpected response structure.", response);
                            }
                        },
                        error: function(error) {
                            console.error("Error fetching employee data", error);
                        }
                    });

                    function fetchLeaveDetails(employeeId, date) {
                        let leaveBalanceElement = root_element.querySelector('#leave-balance-container');

                        console.log("Leave details");
                        console.log("Employee", employeeId);
                        console.log("Date", date);

                        if (!employeeId || !date) {
                            leaveBalanceElement.innerHTML = '<p>Leaves are not allocated.</p>';
                            return;
                        }

                        frappe.call({
                            method: "hrms.hr.doctype.leave_application.leave_application.get_leave_details",
                            args: {
                                employee: employeeId, 
                                date: date             
                            },
                            callback: function(response) {
                                console.log("Leave details response", response);

                                if (response.message && response.message.leave_allocation) {
                                    let leaveAllocation = response.message.leave_allocation;

                                    console.log("leaveAllocation", leaveAllocation);

                                    if (leaveAllocation == null || (typeof leaveAllocation === 'object' && Object.keys(leaveAllocation).length === 0)) {
                                        console.log("Inside leaveAllocation is null or empty");
                                        leaveBalanceElement.innerHTML = '<p>No leaves have been allocated!</p>';
                                        return;  
                                    }

                                    let leaveDetailsHTML = '';
                                    for (let leaveType in leaveAllocation) {
                                        let leaveData = leaveAllocation[leaveType];
                                        leaveDetailsHTML += `
                                            <div class="leave-box">
                                            <img class="leave-icon" src="/files/leave_icon_1.gif" alt="Leave Icon" />
                                                <div class="leave-title"> 
                                                    ${leaveType}
                                                <span class="leave-details">
                                                    Available Leaves: ${leaveData.remaining_leaves || '-'}
                                                </span>
                                                </div>
                                            </div>
                                        `;
                                    }

                                    leaveBalanceElement.innerHTML = leaveDetailsHTML;
                                } else {
                                    leaveBalanceElement.innerHTML = '<p>No leaves have been allocated!</p>';
                                }
                            },
                            error: function(error) {
                                console.log("Error", error);
                                leaveBalanceElement.innerHTML = '<p>Unable to fetch leave details!</p>';
                            }
                        });
                    }
                """,  # Field label
                "style": """ 
                body {
                font-family: Arial, sans-serif;
                background-color: #f4f4f9;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                }

                .workspace-container {
                width: 100%;
                background-color: #ffffff;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                border-radius: 8px;
                overflow: hidden;
                }

                .employee-info {
                display: flex;
                align-items: center;
                padding: 20px;
                background-color: #0055a2;
                color: #ffffff;
                }

                .employee-image {
                width: 80px;
                height: 80px;
                border-radius: 50%;
                margin-right: 15px;
                border: 3px solid #ffffff;
                }

                .employee-details h2 {
                margin: 0;
                font-size: 1.4em;
                }

                .employee-details p {
                margin: 4px 0;
                font-size: 0.9em;
                }

                .leave-balance {
                padding: 20px;
                }

                .leave-balance h3 {
                font-size: 1.2em;
                margin-bottom: 10px;
                color: #333;
                }

                .leave-type {
                display: flex;
                justify-content: space-between;
                padding: 8px 0;
                border-bottom: 1px solid #f0f0f0;
                }

                .leave-type:last-child {
                border-bottom: none;
                }

                .leave-type span {
                font-size: 0.9em;
                color: #666;
                }

                .employee-details {
                width: 100%;
                display: flex;
                flex-direction: row;
                align-items: center;
                justify-content: flex-start;
                gap: 20px;
                }

                .employee-content ul {
                list-style: none;
                padding: 0;
                margin: 0;
                }

                .employee-content-list {
                display: flex;
                flex-direction: row;
                align-items: center;
                gap: 140px;
                }

                .employee-content {
                width: 100%;
                }

                .employee-image-container {
                width: 100px;
                height: 100px;
                overflow: hidden;
                border-radius: 50%;
                margin: 0 auto;
                margin-bottom: 0px;
                }

                .employee-image {
                width: 100%;
                height: 100%;
                object-fit: cover;
                }

                .employee-name {
                text-align: left;
                font-size: 1.5em;
                color: white;
                margin-bottom: 5px;
                }

                .leave-balance-container {
                display: flex;
                flex-wrap: wrap;
                justify-content: space-between;
                padding: 15px;

                
                }

                .leave-box {
                flex: 0 0 30%; 
                box-sizing: border-box;
                padding: 10px;
                margin: 10px;
                border-radius: 8px;
                color: #fff;           
                text-align: left;  
                box-shadow: 0px 0px 5px rgba(0, 0, 0, 0.1);
                transition: transform 0.2s ease-in-out;
                background-color: #d8f0fa; 
                display: flex; 
                align-items: center;
                
                }

                .leave-box:hover {
                transform: scale(1.05);
                }  
                

                .leave-title {
                font-size: 14px;
                margin-bottom: 0px;
                color: #000000;
                font-weight: bold;
                }

                .leave-details {
                margin: 0;
                font-size: 12px;
                color: #000000; 
                    display: block;
                    font-weight:500;
                }


                .leave-content {
                display: flex;                 
                align-items: center;          
                }

                .leave-icon {
                width: 40px;                   
                height: 40px;
                margin-right: 15px;            
                }

                .leave-info {
                display: flex;
                flex-direction: column;       
                }
                """,  
            }).insert()

