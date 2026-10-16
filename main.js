// Token generation fetch call ke response handle karte waqt:
fetch('/api/tokens', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        customer_name: nameInput,
        customer_phone: phoneInput,
        service_type: serviceInput
    })
})
.then(res => res.json())
.then(data => {
    if (data.success) {
        const tokenData = data.data;

        // UI elements update karein
        document.getElementById('token-number').innerText = tokenData.token_number;
        document.getElementById('wait-time').innerText = tokenData.estimated_wait_minutes;

        // WhatsApp Link handle karein
        const waContainer = document.getElementById('whatsapp-btn-container');
        if (tokenData.whatsapp_url) {
            waContainer.innerHTML = `
                <a href="${tokenData.whatsapp_url}" target="_blank" class="whatsapp-btn">
                    💬 Send Ticket to WhatsApp
                </a>
            `;
            
            // OPTIONAL: Automatically open WhatsApp in new tab
            // window.open(tokenData.whatsapp_url, '_blank');
        } else {
            waContainer.innerHTML = '';
        }
    }
});