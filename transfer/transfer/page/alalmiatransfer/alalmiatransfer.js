frappe.pages['alalmiatransfer'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'شركــة العالمــية',
        single_column: true,
    });

    // Hide the sidebar explicitly if it appears
    
    // setTimeout(() => {
    //     $(wrapper).find('.body-sidebar-top').css('display', "none"); // Hides the sidebar
    //     $(wrapper).find('.app-logo').css('display', "none"); // Adjusts the page layout
    // }, 100); // Delay to ensure the DOM is fully loaded

    // Add your company logo and style the page
    $(page.body).html(`
        <div style="text-align: center; margin-top: 20px;">
            <!-- Company Logo -->
            <img src="/assets/transfer/images/logo.png" alt="شركــة العالمــية" style="max-width: 200px; margin-bottom: 20px;">
            
            <!-- Page Title -->
            <h1 style="font-size: 28px; color: #333; margin-bottom: 20px;">مرحباً بكم في شركــة العالمــية</h1>
            
            <!-- Description -->
            <p style="font-size: 16px; color: #555; margin-bottom: 30px;">يرجى اختيار نوع التحويل للمتابعة:</p>

            <!-- Links -->
            <div style="display: flex; justify-content: center; gap: 20px;">
                <a href="/app/internal-transfer" class="btn btn-primary" style="padding: 15px 30px; font-size: 16px;">تحويلات داخلية</a>
                <a href="/app/company-transfer" class="btn btn-primary" style="padding: 15px 30px; font-size: 16px;">تحويلات خارجية</a>
                <a href="/app/transfer-between-branches" class="btn btn-primary" style="padding: 15px 30px; font-size: 16px;">تحويلات بين الفروع</a>
            </div>
        </div>
    `);

};
