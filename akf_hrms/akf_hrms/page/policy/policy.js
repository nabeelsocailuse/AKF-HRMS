let fargs = {"department": ""};
frappe.pages['policy'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Policy',
		single_column: true
	});
	$(frappe.render_template("policy")).appendTo(page.main)
// 	$(frappe.render_template("team_attendance")).appendTo(page.main);
	erpnext.policy.all_policy(fargs);
    refresh.refresh_btn(page)
}

refresh = {
    refresh_btn: function(page){
		
        let department = page.add_field({
            "label": "Department",
            "fieldtype": "Link",
            "fieldname": "department",
			"options": "Department",
            change(){
				fargs["department"] = department.get_value();
                erpnext.policy.all_policy(fargs);
            }
        });
		
		// let rbtn = page.add_field({
        //     "label": "Refresh",
        //     "fieldtype": "Button",
        //     "fieldname": "refresh_btn",
        //     click(){
        //         erpnext.policy.all_policy();
        //     }
        // });
    }
}

erpnext.policy = {
	all_policy: function(fargs) {
		frappe.call({
			method: "akf_hrms.akf_hrms.page.policy.policy.get_policy",
			args: {
				fargs: fargs
			},
			callback: function(r) {	 
				new erpnext.Policy(r.message)
			}
		});
	}
}

let pre_sort=0;
erpnext.Policy = Class.extend({
	init: function(cjo) {
		this.make(cjo);
	},
	make: function(cjo) {
		var html_value = `
	<!-- Required meta tags -->
	<meta charset="utf-8">
	<meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">

	<!-- Bootstrap CSS 
	<link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css" integrity="sha384-Vkoo8x4CGsO3+Hhxv8T/Q5PaXtkKtu6ug5TOeNV6gBiFeWPGFN9MuhOf23Q9Ifjh" crossorigin="anonymous">-->
	<title>Jobs</title>
	<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.12.1/css/all.min.css" integrity="sha256-mmgLkCYLUQbXn0B1SRqzHar6dCnv9oZFPEC1g1cwlkk=" crossorigin="anonymous" />

	<style type="text/css">
		 
        
        .panel {
            border-width: 0 0 1px 0;
            border-style: solid;
            border-color: #fff;
            background: none;
            box-shadow: none;
        }
        
        .panel:last-child {
            border-bottom: none;
        }
        .panel-group > .panel:first-child .panel-heading {
            border-radius: 4px 4px 0 0;
        }
        .panel-group .panel {
            border-radius: 0;
        }
        
        .panel-group .panel + .panel {
            margin-top: 0;
        }
        .panel-heading {
            background-color: #6274fb;
            border-radius: 0;
            border: none;
            color: #fff;
            padding: 0;
        }
        .panel-title a {
            display: block;
            color: #fff;
            padding: 15px;
            position: relative;
            font-size: 22px;
            font-weight: 400;
        }
	.panel-title a:hover,
	.panel-title a:focus{
    		text-decoration: none;
	}

        .panel-heading .btn{
	z-index:5;
position:relative;
	}
        .panel-body {
		background: #fff;
		max-height:300px;
		overflow-y:scroll;
		border: 1px solid #000;
		border-style: dashed;
		border-radius: 10px;
		padding: 10px;
        }

        .panel:last-child .panel-body {
            border-radius: 0 0 4px 4px;
        }
        
        .panel:last-child .panel-heading {
            border-radius: 0 0 4px 4px;
            transition: border-radius 0.3s linear 0.2s;
        }
        
        .panel:last-child .panel-heading.active {
            border-radius: 0;
            transition: border-radius linear 0s;
        }

 .panel-title .btn-primary {
    color: #36414c;
    background-color: #f5f7fa;
    border-color: #ebeff2;
}
        /* #bs-collapse icon scale option */
        
       /* .panel-heading a:before {
            content: '\e146';
            position: absolute;
            font-family: 'Material Icons';
            right: 5px;
            top: 10px;
            font-size: 24px;
            transition: all 0.5s;
            transform: scale(1);
        }
        
        .panel-heading.active a:before {
            content: ' ';
            transition: all 0.5s;
            transform: scale(0);
        }
        
        #bs-collapse .panel-heading a:after {
            content: ' ';
            font-size: 24px;
            position: absolute;
            font-family: 'Material Icons';
            right: 5px;
            top: 10px;
            transform: scale(0);
            transition: all 0.5s;
        }
        
        #bs-collapse .panel-heading.active a:after {
            content: '\e909';
            transform: scale(1);
            transition: all 0.5s;
        }*/
        /* #accordion rotate icon option */
        
        #accordion .panel-heading a:before {
            content: '\e316';
            font-size: 24px;
            position: absolute;
            font-family: 'Material Icons';
            right: 5px;
            top: 10px;
            transform: rotate(180deg);
            transition: all 0.5s;
        }
        
        #accordion .panel-heading.active a:before {
            transform: rotate(0deg);
            transition: all 0.5s;
        }
		.img-settings{
			height: 150px;
		}
		.text-format{
			color: lightgray;
			font-size: 14px;
		}
	</style>
	<br><br>
	<div class="col-md-12 col-sm-12 col-xs-12"> 
            <div class="panel-group wrap" id="bs-collapse">
	`
		let sort_order=0;
		const cjoLength = cjo.length;
		for (var i=0; i < cjoLength; i++) {
			sort_order = i+1;
			html_value += `<div class="panel" sort-order="${sort_order}">
		            			<div class="panel-heading">
		                			<h4 class="panel-title">
								<!-- button id='`+ cjo[i]['policy_file'] +`' class="btn btn-primary apply_now pull-right" style="margin: 9px 10px 0 0;" >Download</button -->
								<a data-toggle="collapse" data-parent="#bs-collapse" href=""> `+ cjo[i]['name'] +`</a>
							</h4>
						</div>
						<div id="${sort_order}" class="panel-collapse collapse">
                            <br>
                            <div style="text-align:center;">
                                <img class="img-settings" src="/files/Logo_001.png" alt="AKFP Header" >  
                            </div>
                            <br>
							<div class="panel-body"> 
								`+ cjo[i]['policy_contents'] +`
							</div>
							<br>
							<!-- div>
								<iframe src="`+ cjo[i]['policy_file'] +`" height="400" width="400" title="description"></iframe>
							</div -->
						</div>

					</div>`
		}
		if(cjoLength==0){
			html_value += `<div class="row">
				<div class="col-md-12">
					<p class="text-center text-format">Not found...</p>
				</div>
			</div>`;
		}
		html_value += `</div></div><!-- end of container -->
<script type="text/javascript">
 $(document).ready(function () {
            $('.collapse.in').prev('.panel-heading').addClass('active');
            $('#accordion, #bs-collapse')
                .on('show.bs.collapse', function (a) {
                    $(a.target).prev('.panel-heading').addClass('active');
                })
                .on('hide.bs.collapse', function (a) {
                    $(a.target).prev('.panel-heading').removeClass('active');
                });
        });
</script>`
		$("#policy").empty();
		$("#policy").html(html_value);

		// $(frm.fields_dict.policy.wrapper).empty();
		// var job_form = $(html_value).appendTo(frm.fields_dict.policy.wrapper);
		// $('.apply_now').click(function(){
		// 	var current_job_click = $(this).attr("id");
		// 	//var url = String(window.location.origin) +'/api/method/frappe.utils.print_format.download_multi_pdf?doctype=Employee Policy Management&name=["' + String(current_job_click) + '"]&format=Standard&no_letterhead=1';
		// 	var url = String(window.location.origin)+ String(current_job_click);
		// 	window.location.href = url;
		// 	//window.open(url);
		// });
		$(".panel").click(function(){
			const temp_sort = $(this).attr("sort-order");
			let isCollapse = $(`#${temp_sort}`).hasClass("collapse");
			// console.log("isCollapse: ", isCollapse);
			// console.log("temp_sort: ", temp_sort);
			// console.log("pre_sort: ", pre_sort);
			if(isCollapse){
				$(`#${temp_sort}`).removeClass("collapse");
				if(pre_sort!=temp_sort){
					$(`#${pre_sort}`).addClass("collapse");
					pre_sort=temp_sort;
				}
			}else{
				$(`#${temp_sort}`).addClass("collapse");
			}
		});
	}
});


