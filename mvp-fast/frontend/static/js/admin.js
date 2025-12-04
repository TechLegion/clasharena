async function markWinner(entryId, isWinner) {
    if (!confirm(`Are you sure you want to ${isWinner ? 'mark' : 'unmark'} this entry as winner?`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/admin/mark-winner', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                entry_id: entryId,
                is_winner: isWinner
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('Winner status updated successfully!');
            location.reload();
        } else {
            alert('Failed to update winner status: ' + (data.message || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred. Please try again.');
    }
}

async function triggerPayout(entryId) {
    if (!confirm('Are you sure you want to trigger payout for this winner?')) {
        return;
    }
    
    try {
        const response = await fetch('/api/admin/trigger-payout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                entry_id: entryId
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('Payout triggered successfully!');
            location.reload();
        } else {
            alert('Failed to trigger payout: ' + (data.message || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred. Please try again.');
    }
}

async function updateWhatsAppLink() {
    const input = document.getElementById('whatsapp-link-input');
    const messageDiv = document.getElementById('whatsapp-link-message');
    const link = input.value.trim();
    
    if (!link) {
        messageDiv.innerHTML = '<span style="color: #ff6b6b;">Please enter a WhatsApp link</span>';
        return;
    }
    
    if (!link.startsWith('http://') && !link.startsWith('https://')) {
        messageDiv.innerHTML = '<span style="color: #ff6b6b;">Please enter a valid URL starting with http:// or https://</span>';
        return;
    }
    
    try {
        messageDiv.innerHTML = '<span style="color: #4ecdc4;">Updating...</span>';
        
        const response = await fetch('/api/admin/update-whatsapp-link', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                whatsapp_link: link
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            messageDiv.innerHTML = '<span style="color: #51cf66;">✓ WhatsApp link updated successfully!</span>';
            setTimeout(() => {
                messageDiv.innerHTML = '';
            }, 3000);
        } else {
            messageDiv.innerHTML = '<span style="color: #ff6b6b;">Failed to update: ' + (data.message || 'Unknown error') + '</span>';
        }
    } catch (error) {
        console.error('Error:', error);
        messageDiv.innerHTML = '<span style="color: #ff6b6b;">An error occurred. Please try again.</span>';
    }
}

// Auto-refresh registration count every 30 seconds
async function refreshRegistrationCount() {
    try {
        const response = await fetch('/api/admin/registration-count');
        const data = await response.json();
        
        if (data.success) {
            const totalRegistrationsEl = document.getElementById('total-registrations');
            const remainingTo100El = document.getElementById('remaining-to-100');
            
            if (totalRegistrationsEl) {
                totalRegistrationsEl.textContent = data.total_registrations;
            }
            
            if (remainingTo100El && !data.milestone_100_reached) {
                remainingTo100El.textContent = data.remaining_to_100;
            }
            
            // If milestone reached, reload page to show milestone notification
            if (data.milestone_100_reached) {
                const milestoneNotified = sessionStorage.getItem('milestone_100_notified');
                if (!milestoneNotified) {
                    sessionStorage.setItem('milestone_100_notified', 'true');
                    // Optionally reload to show milestone banner
                    // location.reload();
                }
            }
        }
    } catch (error) {
        console.error('Error refreshing registration count:', error);
    }
}

// Initialize auto-refresh on page load
document.addEventListener('DOMContentLoaded', function() {
    // Refresh registration count every 30 seconds
    setInterval(refreshRegistrationCount, 30000);
    
    // Also refresh immediately
    refreshRegistrationCount();
    
    // Allow Enter key to update WhatsApp link
    const whatsappInput = document.getElementById('whatsapp-link-input');
    if (whatsappInput) {
        whatsappInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                updateWhatsAppLink();
            }
        });
    }
});

