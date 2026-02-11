// Cancel function for stopping agent
async function cancelGeneration() {
    try {
        const response = await fetch('/api/generate/cancel', {
            method: 'POST'
        });
        const result = await response.json();

        if (currentEventSource) {
            currentEventSource.close();
            currentEventSource = null;
        }

        const logDiv = document.getElementById('generate-log');
        logDiv.innerHTML += `<div style="color: #ef4444; margin: 10px 0; padding: 10px; background: #fee2e2; border-radius: 5px; font-weight: 600;">🛑 ${result.message || 'Generation stopped'}</div>`;

        // Reset buttons
        document.getElementById('start-generation-btn').style.display = 'block';
        document.getElementById('stop-generation-btn').style.display = 'none';

    } catch (error) {
        console.error('Failed to cancel:', error);
        alert('Failed to stop generation');
    }
}
