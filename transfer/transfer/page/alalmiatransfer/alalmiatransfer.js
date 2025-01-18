frappe.pages['alalmiatransfer'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'شركــة العالمــية',
        single_column: true,
    });

    // Inject HTML with responsive styling
    $(page.body).html(`
        <div style="text-align: center; margin-top: 20px;">
            <!-- Company Logo -->
            <img src="/assets/transfer/images/logo.png" alt="شركــة العالمــية" 
                style="max-width: 200px; margin-bottom: 20px; width: 100%; height: auto;">
            
            <!-- Page Title -->
            <h1 style="font-size: 2rem; color: #333; margin-bottom: 20px;">مرحباً بكم في شركــة العالمــية</h1>
            
            <!-- Description -->
            <p style="font-size: 1rem; color: #555; margin-bottom: 30px;">يرجى اختيار نوع التحويل للمتابعة:</p>

            <!-- Links -->
            <div style="
                display: flex; 
                flex-wrap: wrap; 
                justify-content: center; 
                gap: 20px; 
                padding: 10px;
            ">
                <a href="/app/internal-transfer" 
                    class="btn btn-primary" 
                    style="flex: 1; max-width: 200px; padding: 15px; font-size: 1rem; text-align: center;">
                    تحويلات داخلية
                </a>
                <a href="/app/company-transfer" 
                    class="btn btn-primary" 
                    style="flex: 1; max-width: 200px; padding: 15px; font-size: 1rem; text-align: center;">
                    تحويلات خارجية
                </a>
                <a href="/app/transfer-between-branches" 
                    class="btn btn-primary" 
                    style="flex: 1; max-width: 200px; padding: 15px; font-size: 1rem; text-align: center;">
                    تحويلات بين الفروع
                </a>
            </div>
        </div>
    `);
};
