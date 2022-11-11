frappe.ready(function() {
	document.onreadystatechange = () => {
		if (document.readyState === 'complete') {
			setTimeout(check_status(), 1000);
		}
	}
});

function check_status(){
	let status = new RegExp('[\?&]' + "status" + '=([^&#]*)').exec(window.location.href)[1] || '';
	let id = new RegExp('[\?&]' + "id" + '=([^&#]*)').exec(window.location.href)[1] || '';
	if(status && id){
		frappe.call({
			method: "skipcash_integration.www.skipcash.get_payment_info",
			args: {"id": id},
			callback: function(r){
				if(r){
					let data = r.message;
					console.log(data);
					if(data.status == "paid"){
						let payment = `<p>Paid Amount: <b>${data.currency} ${data.amount}</b></p>`;
						let id = `<p>Payment ID: <b>${data.visaId}</b>`;
						let status = `<p>Status: <b>Paid</p></b>`;
						let more_info = `<p style="margin: 15px 0px;"><a href="${data.payUrl}" rel="nofollow" class="btn btn-primary">For More Info</a></p>`;
						$("#info").html(payment+id+status+more_info);
						$(".failed").css("display", "none");
						$(".working").css("display", "none");
						$(".success").css("display", "block");
					}else{
						let payment = `<p>Paid Amount: <b>${data.currency} ${data.amount}</b></p>`;
						let id = `<p>Payment ID: <b>${data.visaId}</b>`;
						let status = `<p>Status: <b>Failed</p></b>`;
						//let more_info = `<p style="margin: 15px 0px;"><a href="${data.payUrl}" rel="nofollow" class="btn btn-primary">Retry</a></p>`;
						$("#failed_info").html(payment+id+status);
						$(".failed").css("display", "block");
						$(".working").css("display", "none");
						$(".success").css("display", "none");
					}
				}
			}
		});
	}else{
		frappe.msgprint("Invalid url")
	}
}
