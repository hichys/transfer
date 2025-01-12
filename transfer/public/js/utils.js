//extract phone number from text(whatsapp_desc) 
// should start with 09 and it follows with 8 digits
function extract_phone_number(whatsapp_desc) {
    try {
        // Clean the text to remove spaces and hyphens
        let cleanedText = whatsapp_desc.replace(/[\s-]/g, "");

        // Match a phone number pattern with or without the country code
        let match = cleanedText.match(/(?:\+?218)?0?(9[1234]\d{7})/);

        if (match) {
            console.log("Matched phone number:", match[1]);
            return '0' + match[1]; // Return the matched phone number
        } else {
            console.log("No valid phone number found.");
            return "ادخل يدويا"; // Fallback if no match
        }
    } catch (error) {
        console.error("Error in extract_phone_number:", error);
        return "ادخل يدويا"; // Fallback for unexpected errors
    }
} 
