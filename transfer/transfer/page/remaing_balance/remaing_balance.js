frappe.pages['remaing-balance'].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Remaining Balance',
		single_column: true
	});

	// Render initial structure with fancy styling
	$(page.body).html(`
        <div style="
            text-align: center; 
            margin-top: 20px; 
            padding: 30px; 
            border: 1px solid #ddd; 
            border-radius: 10px; 
            background: linear-gradient(to bottom, #f9f9f9, #eaeaea);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            max-width: 600px; 
            margin: auto;
        ">
            <!-- Company Logo -->
            <img src="/assets/transfer/images/logo.png" alt="شركــة العالمــية" 
                style="max-width: 150px; margin-bottom: 20px; width: 100%; height: auto;">

            <!-- Page Title -->
            <h2 style="font-size: 1.5rem; color: #333; margin-bottom: 20px;">
                الرصيد المتبقي
            </h2>

            <!-- Currency Descriptions -->
            <div style="
                background: #fff; 
                padding: 15px; 
                border-radius: 8px; 
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                margin-bottom: 20px;
                text-align: right;
                font-size: 1rem;
                color: #555;
            ">
                <p class="rem_bankak" style="margin: 0; font-size: 1.2rem; font-weight: bold; color:rgb(0, 204, 61);">
                    بنكك: Loading...
                </p>
                <p class="rem_cefa" style="margin: 0; font-size: 1.2rem; font-weight: bold; color: #0066cc;">
                    سيفا: Loading...
                </p>
            </div>

<<<<<<< HEAD
           
=======
            <!-- Currency Selection -->
            <p style="font-size: 1rem; color: #666; margin-bottom: 20px;">
                يرجى اختيار نوع العملة للمتابعة:
            </p>

            <!-- Links -->
            <div style="
                display: flex; 
                justify-content: center; 
                gap: 20px;
            ">
                <a href="/app/bin/7d7j1ia291" 
                    class="btn btn-primary" 
                    style="
                        flex: 1; 
                        max-width: 180px; 
                        padding: 15px; 
                        font-size: 1rem; 
                        text-align: center; 
                        border-radius: 5px;
                        background: #007bff; 
                        color: #fff; 
                        text-decoration: none; 
                        transition: background 0.3s;
                    " 
                    onmouseover="this.style.background='#0056b3'" 
                    onmouseout="this.style.background='#007bff'">
                    بنكك 
                </a>
                <a href="/app/company-transfer" 
                    class="btn btn-primary" 
                    style="
                        flex: 1; 
                        max-width: 180px; 
                        padding: 15px; 
                        font-size: 1rem; 
                        text-align: center; 
                        border-radius: 5px;
                        background: #28a745; 
                        color: #fff; 
                        text-decoration: none; 
                        transition: background 0.3s;
                    " 
                    onmouseover="this.style.background='#1c7430'" 
                    onmouseout="this.style.background='#28a745'">
                    سيفا 
                </a>
            </div>
>>>>>>> 648900c (Merge pull request #8 from hichys/develop)
        </div>
    `);

	// Fetch rem_bankak and update dynamically
	frappe.call({
		method: "transfer.transfer.api.get_rem_bankak",
		args: {},
		callback: function (r) {
			if (r.message) {
				const rem_bankak = r.message;
				$(page.body).find(".rem_bankak").html(`بنكك:  ${rem_bankak}`);
			}
		}
	});

	// Fetch rem_cefa and update dynamically
	frappe.call({
		method: "transfer.transfer.api.get_rem_cefa",
		args: {},
		callback: function (r) {
			if (r.message) {
				const rem_cefa = r.message;
				$(page.body).find(".rem_cefa").html(`سيفا:  ${rem_cefa}`);
			}
		}
	});
};
