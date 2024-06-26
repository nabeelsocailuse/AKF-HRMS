// let filtercom = null

let filters = {};
frappe.pages['hr-dashboard'].on_page_load = async function (wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'HR Dashboard',
        single_column: true
    });
    await filters.add(page);
}

filters = {
    add: function(page){
        
        company = page.add_field({ 
            fieldname: "company",
            label: __("Company"),
            fieldtype: "Link",
            options: "Company",
            default: frappe.defaults.get_default("company"),
            reqd: 1,
            change: (e) => {
                if (e.target.value) {
                    fetchDashboardData(page);
                } else {
                    frappe.msgprint(__("Please select a company"));
                }
            },
        });
    
        let branch = page.add_field({
            fieldname: "branch",
            label: __("Branch"),
            fieldtype: "Link",
            options: "Branch",
            default: "",
            reqd: 0,
            change: (e) => {
                fetchDashboardData(page);
            },
        });

        let fromDateChanged = false;
        let toDateChanged = false;

        let today = new Date(); 
        let lastMonth = new Date(today.getFullYear(), today.getMonth() - 1, 21);
        let fromDate = frappe.datetime.obj_to_str(lastMonth);
        let thisMonth = new Date(today.getFullYear(), today.getMonth(), 20);
        let toDate = frappe.datetime.obj_to_str(thisMonth);

        let from_date = page.add_field({
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date",
            options: "",
            default: fromDate,
            reqd: 0,
            change: (e) => {
                if (new Date(from_date.get_value()) > new Date(to_date.get_value())) {
                    if (!fromDateChanged) {
                        frappe.msgprint(__("From Date cannot be greater than To Date"));
                        fromDateChanged = true;
                        toDateChanged = false;
                    }
                    from_date.set_value(to_date.get_value());
                } else {
                    fromDateChanged = false;
                }
                fetchDashboardData(page);
            },
        });

        let to_date = page.add_field({
            fieldname: "to_date",
            label: __("To Date"),
            fieldtype: "Date",
            options: "",
            default: toDate,
            reqd: 0,
            change: (e) => {
                if (new Date(to_date.get_value()) < new Date(from_date.get_value())) {
                    if (!toDateChanged) {
                        frappe.msgprint(__("To Date cannot be less than From Date"));
                        toDateChanged = true;
                        fromDateChanged = false;
                    }
                    to_date.set_value(from_date.get_value());
                } else {
                    toDateChanged = false;
                }
                fetchDashboardData(page);
            },
        });


        function fetchDashboardData(page) {
            
            filters = {
                "company": company.get_value(),
                "branch": branch.get_value(),
                "from_date": from_date.get_value(),
                "to_date": to_date.get_value(),
            }
            setTimeout(() => {
                serverCall.hr_counts(page, filters);
            }, 0);
            setTimeout(() => {
                serverCall.hr_charts(filters);
            }, 600);
            setTimeout(() => {
                serverCall.recruiment_counts(filters);
            }, 800);
            setTimeout(() => {
                serverCall.recruitment_charts(filters);
            }, 1000);
        }

        let filters_btn = page.add_field({
            fieldname: "filters_btn",
            label: __("Filters"),
            fieldtype: "Button",
            options: "",
            default: "",
            reqd: 0,
            click: (e) => {
                fetchDashboardData(page);
            },
        });

        fetchDashboardData(page);
        
    }
}
serverCall = {
    hr_counts: function(page, filters){
        frappe.call({
            method: "akf_hrms.akf_hrms.page.hr_dashboard.hr_dashboard.get_hr_counts",
            args: {
                filters: filters
            }, 
            callback: function(r){
                let data = r.message;
                design.set_hr_cards(page, data);
            }
        })
    },
    hr_charts: function(filters){
        frappe.call({
            method: "akf_hrms.akf_hrms.page.hr_dashboard.hr_dashboard.get_hr_charts",
            args: {
                filters: filters
            }, 
            callback: function(r){
                let data = r.message;
                design.set_hr_charts(data);
            }
        })
    },
    recruiment_counts: function(filters){
        frappe.call({
            method: "akf_hrms.akf_hrms.page.hr_dashboard.hr_dashboard.get_recruitement_counts",
            args: {
                filters: filters
            }, 
            callback: function(r){
                let data = r.message;
                design.set_recruitment_cards(data);
            }
        })
    },
    recruitment_charts: function(filters){
        frappe.call({
            method: "akf_hrms.akf_hrms.page.hr_dashboard.hr_dashboard.get_recruitement_charts",
            args: {
                filters: filters
            }, 
            callback: function(r){
                let data = r.message;
                design.set_recruitment_charts(data);
            }
        })
    }
}
design = {
    set_hr_cards: function (page, data) {
        $("#management_dashboard_id").remove();
        const content = frappe.render_template("hr_dashboard", data);
        const main = page.main;
        $(content).appendTo(main);
        design.set_update_department_list(data.department_list);
        _triggers_.search();
    },
    set_hr_charts: function(data){
        chartsFunc.employee_count_by_status(data.count_by_employment_type);
        chartsFunc.employee_count_by_department(data.department_wise);
        chartsFunc.employee_count_by_salary_range(data.salary_range);
        chartsFunc.employee_check_in_and_late_entry(data.employee_check_in_and_late_entry);
    },
    set_recruitment_cards: function (data) {
        design.set_recruitment_totals(data);
    },
    set_recruitment_charts: function(data){
        chartsFunc.open_position_by_dept(data.open_position_by_dept);
        chartsFunc.applications_received_by_source(data.applications_received_by_source);
    },
    set_update_department_list: function(values){
        $("#departments").empty();
		$("#departments").html(values);
        search_departments();
    },
    set_recruitment_totals: function(data){
        $("#total_applicants").empty();
        $("#total_applicants").html(data.total_applicants);

        $("#shortlisted").empty();
        $("#shortlisted").html(data.shortlisted_candidates);

        $("#hired").empty();
        $("#hired").html(data.hired_candidates);

        $("#rejected").empty();
        $("#rejected").html(data.rejected_candidates);

        $("#time_to_fill").empty();
        $("#time_to_fill").html(data.time_to_fill);
    }
}

_triggers_ = {
    search: function(){
        $("#department").on('change', function() {
            var department = $(this).val();
            filters["department"] = department;
            setTimeout(() => {
                serverCall.recruiment_counts(filters);   
            }, 100);
            setTimeout(() => {
                serverCall.recruitment_charts(filters);   
            }, 400);
        });
    }
}

chartsFunc = {
    employee_count_by_status: function (data) {
        CountEmploymentType(data); 
    },
    employee_count_by_department: function (data) {
        barChart(data);
    },
    employee_count_by_salary_range: function (data) {
        pieChart(data);
    },
    open_position_by_dept: function(data){
        OpenPositionChart(data);
    },

	applications_received_by_source: function(data){
		ApplicationBySource(data);
	},

	employee_check_in_and_late_entry: function(data){
		EmployeeCheckInOut(data);
	},

	get_department_list: function(values){
		$("#browsers").empty();
		$("#browsers").html(values);
	},	
}
// function EmployeeCheckInOut(data) {
//     Highcharts.chart('employee_by_time', {
//         chart: {
//             type: 'pie' // Change chart type to pie
//         },
//         title: {
//             text: 'Employee Check-In and Late Entry',
//             align: 'left',
//             style: {
//                 fontSize: '18px',
//                 fontWeight: '600',
//                 fontFamily: '"Inter", sans-serif'
//             }
//         },
//         subtitle: {
//             align: 'left',
//             text: ''
//         },
//         exporting: {
//             enabled: false,
//         },
//         credits: {
//             enabled: false
//         },
//         accessibility: {
//             announceNewData: {
//                 enabled: true
//             }
//         },
//         tooltip: {
//             pointFormat: '<span style="color:{point.color}">{point.name}</span>: ' +
//                 '<b>{point.y}</b> of total<br/>'
//         },
//         plotOptions: {
//             pie: {
//                 allowPointSelect: true,
//                 cursor: 'pointer',
//                 dataLabels: {
//                     enabled: true,
//                     format: '{point.name}: {point.y}'
//                 },
//                 showInLegend: true
//             }
//         },
//         series: [{
//             name: 'Count',
//             colorByPoint: true,
//             data: data.map(item => ({ name: item.entry_status, y: item.total }))
//         }]
//     });
// }


function EmployeeCheckInOut(data) {
    // Prepare data for the pie chart
    let chartData = [];
    
    // Loop through data and populate chartData with required format
    data.forEach(item => {
        chartData.push({ name: item.entry_status, y: item.entry_status === 'Late' ? item.late_count : item.on_time_count });
    });
    
    // Generate the Highcharts pie chart
    Highcharts.chart('employee_by_time', {
        chart: {
            type: 'pie'
        },
        title: {
            text: 'Employee Check-In and Late Entry',
            align: 'left',
            style: {
                fontSize: '18px',
                fontWeight: '600',
                fontFamily: '"Inter", sans-serif'
            }
        },
        subtitle: {
            align: 'left',
            text: ''
        },
        exporting: {
            enabled: false
        },
        credits: {
            enabled: false
        },
        accessibility: {
            announceNewData: {
                enabled: true
            }
        },
        tooltip: {
            pointFormat: '<span style="color:{point.color}">{point.name}</span>: ' +
                '<b>{point.y}</b> of total<br/>'
        },
        plotOptions: {
            pie: {
                allowPointSelect: true,
                cursor: 'pointer',
                dataLabels: {
                    enabled: true,
                    format: '{point.name}: {point.y}'
                },
                showInLegend: true
            }
        },
        series: [{
            name: 'Count',
            colorByPoint: true,
            data: chartData
        }]
    });
}

function CountEmploymentType(data) {
	Highcharts.chart('employee_by_status', {
		colors: ['#01BAF2', 'rgb(75, 208, 139)', '#FAA74B', '#B37CD2'],
		chart: {
			type: 'pie',
		},
		title: {
			text: 'Employee count by employment type', 
			align: 'left',
			style: {
				fontSize: '18px', 
				fontWeight: '600',
				fontFamily: '"Inter", sans-serif'
			}
		},
		tooltip: {
			// valueSuffix: '%'
			pointFormat: '<b>{point.name}</b><br>{point.percentage:.1f}%'
		},
		plotOptions: {
			pie: {
				allowPointSelect: true,
				cursor: 'pointer',
				dataLabels: {
					enabled: true,
					format: '{point.name}: {y} '
				},
				showInLegend: true
			}
		},
		legend: {
			align: 'left',
			verticalAlign: 'bottom',
			layout: 'horizontal',
			labelFormat: '<b>{name}</b>',
			itemWidth: 150 
		},
		series: [{
			name: 'Percentage',
			colorByPoint: true,
			innerSize: '80%',
			data: data
		}],
		credits: {
			enabled: false 
		}
	});
}
function OpenPositionChart(data) {
	Highcharts.chart('open_position', {
		colors: ['#01BAF2', 'rgb(75, 208, 139)', '#FAA74B', '#B37CD2'],
		chart: {
			type: 'pie',
		},
		title: {
			text: 'Open Position By Department',
			align: 'left',
			style: {
				fontSize: '18px', 
				fontWeight: '600',
				fontFamily: '"Inter", sans-serif'
			}
		},
		tooltip: {
			 pointFormat: '<b>{point.name}</b><br>{point.percentage:.1f}%'
			// valueSuffix: '%'
		},
		plotOptions: {
			pie: {
				allowPointSelect: true,
				cursor: 'pointer',
				dataLabels: {
					enabled: true,
					// format: '{point.name}: {y} %'
					format: '{point.name}: {y}'
				},
				showInLegend: true
			}
		},
		legend: {
			align: 'left',
			verticalAlign: 'bottom',
			layout: 'horizontal',
			labelFormat: '<b>{name}</b>',
			itemWidth: 150 
		},
		series: [{
			name: 'Percentage',
			colorByPoint: true,
			innerSize: '80%',
			data: data
		}],
		credits: {
			enabled: false 
		}
	});
}
function barChart(data) {
	Highcharts.chart('employee_count', {
		chart: {
			type: 'column'
		}, 
		title: {
			text: 'Employee count By department',
			align: 'left',
			style: {
				fontSize: '18px', 
				fontWeight: '600',    
				fontFamily: '"Inter", sans-serif'
			}
		},
		subtitle: {
			align: 'left',
			text: ''
		},
		exporting: {
			enabled: false,
		},
		credits: {
			enabled: false
		},
		accessibility: {
			announceNewData: {
				enabled: true
			}
		},
		xAxis: {
			type: 'category'
		},
		yAxis: {
			title: {
				text: ''
			}
		},
		legend: {
			enabled: false
		},
		plotOptions: {
			series: {
				borderWidth: 0,
				dataLabels: {
					enabled: true,
					format: '{point.y}'
				}
			}
		},
		tooltip: {
			headerFormat: '<span style="font-size:11px">{series.name}</span><br>',
			pointFormat: '<span style="color:{point.color}">{point.name}</span>: ' +
				'<b>{point.y}</b> of total<br/>'
		},
		series: [{
			name: 'Employees',
			colorByPoint: true,
			data: data
		
		}]
	});
}
function ApplicationBySource(data) {
    Highcharts.chart('application_received', {
        chart: {
            type: 'column'
        }, 
        title: {
            text: 'Application Received By Source',
            align: 'left',
            style: {
                fontSize: '18px', 
                fontWeight: '600',    
                fontFamily: '"Inter", sans-serif'
            }
        },
        subtitle: {
            align: 'left',
            text: ''
        },
        exporting: {
            enabled: false,
        },
        credits: {
            enabled: false
        },
        accessibility: {
            announceNewData: {
                enabled: true
            }
        },
        xAxis: {
            type: 'category'
        },
        yAxis: {
            title: {
                text: ''
            },
            allowDecimals: false, // This will disable decimal values on y-axis
            labels: {
                formatter: function() {
                    return Math.floor(this.value); // Ensures only whole numbers are displayed
                }
            }
        },
        legend: {
            enabled: false
        },
        plotOptions: {
            series: {
                borderWidth: 0,
                dataLabels: {
                    enabled: true,
                    format: '{point.y}'
                }
            }
        },
        tooltip: {
            headerFormat: '<span style="font-size:11px">{series.name}</span><br>',
            pointFormat: '<span style="color:{point.color}">{point.name}</span>: ' +
                '<b>{point.y}</b> of total<br/>'
        },
        series: [{
            name: 'Applications',
            colorByPoint: true,
            data: data
        }]
    
    });
}
function pieChart(data) {
	Highcharts.chart('salary_range', {
		chart: {
			type: 'pie'
		}, 
		title: {
			text: 'Employee count By salary range',
			align: 'left',
			style: {
				fontSize: '18px', 
				fontWeight: '600',
				fontFamily: '"Inter", sans-serif'
			}
		},
		subtitle: {
			text: ''
		},
		exporting: {
			enabled: false,
		},
		credits: {
			enabled: false
		},
		plotOptions: {
			series: {
				showInLegend: true,
				allowPointSelect: true,
				cursor: 'pointer',
				dataLabels: [{
					enabled: false,
					distance: 20
				}, {
					enabled: true,
					distance: -40,
					format: '{point.y}',
					style: {
						fontSize: '1.2em',
						textOutline: 'none',
						opacity: 0.7
					},
					filter: {
						operator: '>',
						property: 'percentage',
						value: 10
					}
				}]
			}
		},
		series: [{
			name: 'Employees',
			colorByPoint: true,
			data: data
		}]
	});
}

// HR Recruitment Dashboard
function search_departments() {
    $("#department").on('change', function() {
        console.log(company)
        var selectedValue = $(this).val();
        // updateTotalCandidates(selectedValue);
        // updateShortlistedCandidates(selectedValue);
        // updateHiredCandidates(selectedValue);
        // updateRejectedCandidates(selectedValue);
        // updateTimetoFill(selectedValue);
    });
}
function updateTotalCandidates(department, company) {
 
    frappe.call({
        method: 'akf_hrms.akf_hrms.page.hr_dashboard.hr_dashboard.department_wise_count',
        args: {
            filters: {
                "department": department,
                "company": company
            }
        },
        callback: function(r) {
            if (r.message) {
                if (r.message.error) {
                    console.error("Error fetching Total candidates:", r.message.error);
                } else if (r.message.total !== undefined) {
                    console.log("Shortlisted candidates count:", r.message);
                    document.querySelector('.card .applicant_count').textContent = r.message.total;
                    const data = r.message.total;
                    const t1 = document.getElementById('total_applicants');
                    if (t1) {
                        t1.textContent = data;
                    } else {
                        console.error("Element with id 'total_applicants' not found.");
                    }
                } else {
                    console.error("Unexpected response structure:", r.message);
                }
            } else {
                console.error("Error fetching Total candidates:", r.exc);
            }
        },
        error: function(xhr, status, error) {
            console.error("Error occurred while fetching Total candidates:", error);
        }
    });
}
function updateShortlistedCandidates(department) {
    frappe.call({
        method: 'akf_hrms.akf_hrms.page.hr_dashboard.hr_dashboard.get_shortlisted_candidates',
        args: {
            filters: { "department": department }
        },
        callback: function(r) {
            console.log(r.message)
            if (r.message) {
                if (r.message.error) {
                    console.error("Error fetching shortlisted candidates:", r.message.error);
                } else if (r.message.total !== undefined) {
                    console.log("Shortlisted candidates count:", r.message);
                    document.querySelector('.card .applicant_count').textContent = r.message.total;
                    const data = r.message.total
                    t1 = document.getElementById('shortlisted')
                    if (t1) {
                        t1.textContent = ''; 
                        t1.append(data);
                    } else {
                        console.error("Element with ID 'shortlisted' not found.");
                    }
                    // t1.append(data)
                    // document.querySelector('.card .applicant_count').textContent = r.message.count;
                } else {
                    // console.error("Unexpected response structure:", r.message);
                }
            } else {
                console.error("Error fetching shortlisted candidates:", r.exc);
            }
        },
        error: function(xhr, status, error) {
            console.error("Error occurred while fetching shortlisted candidates:", error);
        }
    });
}
function updateHiredCandidates(department) {
    frappe.call({
        method: 'akf_hrms.akf_hrms.page.hr_dashboard.hr_dashboard.get_hired_candidates',
        args: {
            filters: { "department": department }
        },
        callback: function(r) {
            console.log(r.message)
            if (r.message) {
                if (r.message.error) {
                    console.error("Error fetching hired candidates:", r.message.error);
                } else if (r.message.total !== undefined) {
                    console.log("Hired candidates count:", r.message);
                    document.querySelector('.card .applicant_count').textContent = r.message.total;
                    const data = r.message.total;
                    const t1 = document.getElementById('hired');
                    if (t1) {
                        t1.textContent = ''; 
                        t1.append(data);
                    } else {
                        console.error("Element with ID 'hired' not found.");
                    }
                } else {
                    // console.error("Unexpected response structure:", r.message);
                }
            } else {
                console.error("Error fetching hired candidates:", r.exc);
            }
        },
        error: function(xhr, status, error) {
            console.error("Error occurred while fetching hired candidates:", error);
        }
    });
}
function updateRejectedCandidates(department) {
    frappe.call({
        method: 'akf_hrms.akf_hrms.page.hr_dashboard.hr_dashboard.get_rejected_candidates',
        args: {
            filters: { "department": department }
        },
        callback: function(r) {
            console.log(r.message)
            if (r.message) {
                if (r.message.error) {
                    console.error("Error fetching rejected candidates:", r.message.error);
                } else if (r.message.total !== undefined) {
                    console.log("Rejected candidates count:", r.message);
                    document.querySelector('.card .applicant_count').textContent = r.message.total;

                    const data = r.message.total;
                    const t1 = document.getElementById('rejected');
                    if (t1) {
                        t1.textContent = ''; 
                        t1.append(data);
                    } else {
                        t1.append(data);
                    }
                } else {
                    // console.error("Unexpected response structure:", r.message);
                }
            } else {
                console.error("Error fetching rejected candidates:", r.exc);
            }
        },
        error: function(xhr, status, error) {
            console.error("Error occurred while fetching rejected candidates:", error);
        }
    });
}
function updateTimetoFill(department) {
    frappe.call({
        method: 'akf_hrms.akf_hrms.page.hr_dashboard.hr_dashboard.job_requisition',
        args: {
            filters: { "department": department }
        },
        callback: function(r) {
            console.log(r.message);
            if (r.message) {
                if (r.message.error) {
                    console.error("Error fetching average time to fill:", r.message.error);
                } else {
                    console.log("Average time to fill:", r.message);
                    const avgTime = r.message;
                    document.querySelector('.card .applicant_count').textContent = r.message;

                    const data = r.message.total;
                    const t1 = document.getElementById('time_to_fill');
                    if (t1) {
                        t1.textContent = ''; 
                        t1.append(data);
                    } else {
                        t1.append(data);
                    }
                }
            } else {
                console.error("Error fetching average time to fill:", r.exc);
            }
        },
        error: function(xhr, status, error) {
            console.error("Error occurred while fetching average time to fill:", error);
        }
    });
}