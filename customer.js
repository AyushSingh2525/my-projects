function initCustomerTracker(tokenId) {
    const socket = io();

    const elements = {
        tokenDisplay: document.getElementById('tokenDisplay'),
        customerName: document.getElementById('customerName'),
        serviceType: document.getElementById('serviceType'),
        tokenStatus: document.getElementById('tokenStatus'),
        tokensAhead: document.getElementById('tokensAhead'),
        currentServing: document.getElementById('currentServing'),
        connectionStatus: document.getElementById('connectionStatus')
    };

    // Fetch full initial state via API
    function fetchCurrentStatus() {
        fetch(`/api/token_status/${tokenId}`)
            .then(res => {
                if (!res.ok) throw new Error('Token not found');
                return res.json();
            })
            .then(data => {
                updateUI(data);
            })
            .catch(err => {
                elements.tokenStatus.innerText = "Error Loading";
                console.error("Status fetch error:", err);
            });
    }

    // Update DOM elements
    function updateUI(data) {
        elements.tokenDisplay.innerText = data.token_number;
        elements.customerName.innerText = data.customer_name;
        elements.serviceType.innerText = data.service_type;
        
        elements.tokenStatus.innerText = data.status.toUpperCase();
        elements.tokenStatus.className = `badge badge-${data.status}`;
        
        elements.tokensAhead.innerText = data.tokens_ahead;
        elements.currentServing.innerText = data.currently_serving;
    }

    // --- SOCKET EVENT HANDLERS ---

    socket.on('connect', () => {
        elements.connectionStatus.innerText = "● Live Sync Active";
        elements.connectionStatus.className = "connection-indicator connected";
        
        // Fetch current status upon connecting/reconnecting
        fetchCurrentStatus();
    });

    socket.on('disconnect', () => {
        elements.connectionStatus.innerText = "○ Reconnecting...";
        elements.connectionStatus.className = "connection-indicator disconnected";
    });

    // Listen for global queue updates from admin
    socket.on('queue_updated', (data) => {
        // Re-evaluate queue position and active serving token whenever state changes
        fetchCurrentStatus();
    });
}