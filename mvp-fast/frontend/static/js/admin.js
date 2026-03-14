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
    if (!confirm('Are you sure you want to trigger payout for this player?')) {
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

async function bulkPayout() {
    if (!confirm('Process payout for ALL players with pending status? Amount = kills × per_kill_value × exchange_rate')) {
        return;
    }
    try {
        const response = await fetch('/api/admin/bulk-payout', { method: 'POST' });
        const data = await response.json();
        if (data.success) {
            alert(`Bulk payout complete! Processed: ${data.processed} of ${data.total_pending}. ${data.errors?.length ? 'Errors: ' + data.errors.length : ''}`);
            location.reload();
        } else {
            alert('Bulk payout failed: ' + (data.detail || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred. Please try again.');
    }
}

async function updateKillCount(entryId, killCount) {
    const count = parseInt(killCount, 10);
    if (isNaN(count) || count < 0) return;
    try {
        const response = await fetch('/api/admin/update-kill-count', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ entry_id: entryId, kill_count: count })
        });
        const data = await response.json();
        if (data.success) {
            // Optional: show brief feedback
        } else {
            alert('Failed to update kill count');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Failed to update kill count');
    }
}

async function updateCodLobbyLink() {
    const input = document.getElementById('cod-lobby-link-input');
    const messageDiv = document.getElementById('cod-lobby-message');
    const link = input.value.trim();
    try {
        messageDiv.innerHTML = '<span class="admin-msg-success">Updating...</span>';
        const response = await fetch('/api/admin/update-cod-lobby-link', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ cod_lobby_link: link })
        });
        const data = await response.json();
        if (data.success) {
            messageDiv.innerHTML = '<span class="admin-msg-success">✓ COD lobby link updated</span>';
            setTimeout(() => { messageDiv.innerHTML = ''; }, 3000);
        } else {
            messageDiv.innerHTML = '<span class="admin-msg-error">Failed: ' + (data.detail || 'Unknown error') + '</span>';
        }
    } catch (error) {
        messageDiv.innerHTML = '<span class="admin-msg-error">An error occurred.</span>';
    }
}

async function updateTournamentStatus() {
    const select = document.getElementById('tournament-status-select');
    const status = select.value;
    try {
        const response = await fetch('/api/admin/update-tournament-status', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status })
        });
        const data = await response.json();
        if (data.success) {
            // Status updated
        } else {
            alert('Failed to update status');
        }
    } catch (error) {
        alert('Failed to update tournament status');
    }
}

async function removePlayer(entryId) {
    if (!confirm('Remove this player from active list? (Details incorrect - they will be excluded from lobby check and payouts)')) return;
    try {
        const response = await fetch('/api/admin/remove-player', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ entry_id: entryId })
        });
        const data = await response.json();
        if (data.success) { location.reload(); } else { alert('Failed: ' + (data.detail || 'Unknown error')); }
    } catch (e) { alert('Error removing player'); }
}

async function restorePlayer(entryId) {
    try {
        const response = await fetch('/api/admin/restore-player', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ entry_id: entryId })
        });
        const data = await response.json();
        if (data.success) { location.reload(); } else { alert('Failed'); }
    } catch (e) { alert('Error restoring player'); }
}

async function lobbyCrossCheck() {
    const textarea = document.getElementById('lobby-ids-input');
    const resultDiv = document.getElementById('lobby-check-result');
    const ids = textarea.value.split('\n').map(s => s.trim()).filter(Boolean);
    if (ids.length === 0) {
        resultDiv.innerHTML = '<span class="admin-msg-error">Enter at least one CODM ID</span>';
        resultDiv.style.display = 'block';
        return;
    }
    try {
        resultDiv.innerHTML = '<span class="admin-msg-success">Checking...</span>';
        resultDiv.style.display = 'block';
        const response = await fetch('/api/admin/lobby-cross-check', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ lobby_player_ids: ids })
        });
        const data = await response.json();
        if (data.success) {
            let html = '<p><strong>✓ Matches (' + data.match_count + '):</strong> ' + (data.matches.length ? data.matches.join(', ') : 'None') + '</p>';
            html += '<p><strong style="color: var(--admin-danger);">In lobby, not registered (' + data.in_lobby_not_registered.length + '):</strong> ' + (data.in_lobby_not_registered.length ? data.in_lobby_not_registered.join(', ') : 'None') + '</p>';
            html += '<p><strong style="color: var(--admin-accent);">Registered, not in lobby (' + data.in_sheets_not_in_lobby.length + '):</strong> ' + (data.in_sheets_not_in_lobby.length ? data.in_sheets_not_in_lobby.join(', ') : 'None') + '</p>';
            resultDiv.innerHTML = html;
        } else {
            resultDiv.innerHTML = '<span class="admin-msg-error">Check failed</span>';
        }
    } catch (error) {
        resultDiv.innerHTML = '<span class="admin-msg-error">Error: ' + error.message + '</span>';
    }
}

async function updateWhatsAppLink() {
    const input = document.getElementById('whatsapp-link-input');
    const messageDiv = document.getElementById('whatsapp-link-message');
    const link = input.value.trim();
    
    if (!link) {
        messageDiv.innerHTML = '<span class="admin-msg-error">Please enter a WhatsApp link</span>';
        return;
    }
    
    if (!link.startsWith('http://') && !link.startsWith('https://')) {
        messageDiv.innerHTML = '<span class="admin-msg-error">Please enter a valid URL starting with http:// or https://</span>';
        return;
    }
    
    try {
        messageDiv.innerHTML = '<span class="admin-msg-success">Updating...</span>';
        
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
            messageDiv.innerHTML = '<span class="admin-msg-success">✓ WhatsApp link updated</span>';
            setTimeout(() => {
                messageDiv.innerHTML = '';
            }, 3000);
        } else {
            messageDiv.innerHTML = '<span class="admin-msg-error">Failed: ' + (data.message || 'Unknown error') + '</span>';
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
            
            if (totalRegistrationsEl) {
                totalRegistrationsEl.textContent = data.total_registrations;
            }
            
            const remainingToMilestoneEl = document.getElementById('remaining-to-milestone');
            if (remainingToMilestoneEl && !data.milestone_reached) {
                remainingToMilestoneEl.textContent = data.remaining_to_milestone;
            }
            
            // If milestone reached, reload page to show milestone notification
            if (data.milestone_reached) {
                const milestoneNotified = sessionStorage.getItem(`milestone_${data.milestone_threshold}_notified`);
                if (!milestoneNotified) {
                    sessionStorage.setItem(`milestone_${data.milestone_threshold}_notified`, 'true');
                    // Optionally reload to show milestone banner
                    // location.reload();
                }
            }
        }
    } catch (error) {
        console.error('Error refreshing registration count:', error);
    }
}

async function createAdminUser() {
    const usernameInput = document.getElementById('admin-username-input');
    const emailInput = document.getElementById('admin-email-input');
    const passwordInput = document.getElementById('admin-password-input');
    const messageDiv = document.getElementById('admin-user-message');
    
    const username = usernameInput.value.trim();
    const email = emailInput.value.trim();
    const password = passwordInput.value;
    
    // Validation
    if (!username || username.length < 3) {
        messageDiv.innerHTML = '<span class="admin-msg-error">Username must be at least 3 characters</span>';
        return;
    }
    
    if (!password || password.length < 6) {
        messageDiv.innerHTML = '<span class="admin-msg-error">Password must be at least 6 characters</span>';
        return;
    }
    
    if (email && !email.includes('@')) {
        messageDiv.innerHTML = '<span class="admin-msg-error">Please enter a valid email address</span>';
        return;
    }
    
    try {
        messageDiv.innerHTML = '<span class="admin-msg-success">Creating...</span>';
        
        const response = await fetch('/api/admin/create-admin-user', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: username,
                email: email || null,
                password: password
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            messageDiv.innerHTML = '<span class="admin-msg-success">✓ Admin user created</span>';
            // Clear form
            usernameInput.value = '';
            emailInput.value = '';
            passwordInput.value = '';
            // Refresh admin users list
            loadAdminUsers();
            setTimeout(() => {
                messageDiv.innerHTML = '';
            }, 3000);
        } else {
            messageDiv.innerHTML = '<span class="admin-msg-error">Failed: ' + (data.message || 'Unknown error') + '</span>';
        }
    } catch (error) {
        console.error('Error:', error);
        messageDiv.innerHTML = '<span class="admin-msg-error">An error occurred. Please try again.</span>';
    }
}

async function loadAdminUsers() {
    try {
        const response = await fetch('/api/admin/admin-users');
        const data = await response.json();
        
        const container = document.getElementById('admin-users-container');
        
        if (data.success && data.admins && data.admins.length > 0) {
            let html = '';
            data.admins.forEach(admin => {
                const statusBadge = admin.is_active 
                    ? '<span class="admin-user-status">● Active</span>'
                    : '<span style="color: var(--admin-danger); font-size: 12px;">● Inactive</span>';
                html += `<div class="admin-user-card">
                    <div class="admin-user-info"><strong>${admin.username}</strong><span>${admin.email || 'No email'}</span><span style="display:block;margin-top:4px;font-size:11px;">${new Date(admin.created_at).toLocaleDateString()}</span></div>
                    <div>${statusBadge}</div>
                </div>`;
            });
            container.innerHTML = html;
        } else {
            container.innerHTML = '<p style="color: var(--admin-text-muted);">No admin users</p>';
        }
    } catch (error) {
        console.error('Error loading admin users:', error);
        const container = document.getElementById('admin-users-container');
        container.innerHTML = '<p class="admin-msg-error">Error loading admin users</p>';
    }
}

// Initialize auto-refresh on page load
document.addEventListener('DOMContentLoaded', function() {
    // Refresh registration count every 30 seconds
    setInterval(refreshRegistrationCount, 30000);
    
    // Also refresh immediately
    refreshRegistrationCount();
    
    // Load admin users on page load
    loadAdminUsers();
    
    // Allow Enter key to update WhatsApp link
    const whatsappInput = document.getElementById('whatsapp-link-input');
    if (whatsappInput) {
        whatsappInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                updateWhatsAppLink();
            }
        });
    }
    
    // Allow Enter key to create admin user
    const passwordInput = document.getElementById('admin-password-input');
    if (passwordInput) {
        passwordInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                createAdminUser();
            }
        });
    }
});

