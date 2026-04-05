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

function syncRegistrationLobbyNameUI(name) {
    const input = document.getElementById('registration-lobby-name-input');
    const disp = document.getElementById('registration-lobby-name-display');
    const v = name != null && name !== undefined ? String(name) : '';
    if (input) input.value = v;
    if (disp) disp.textContent = v.trim() ? v : '—';
}

function syncOpsStripLobbyCycle(lobbyName, epoch) {
    const lob = document.getElementById('admin-ops-strip-lobby');
    const cyc = document.getElementById('admin-ops-strip-cycle');
    if (lob && lobbyName !== undefined) {
        const t = lobbyName != null ? String(lobbyName).trim() : '';
        lob.textContent = t ? t : '—';
    }
    if (cyc != null && epoch !== undefined && epoch !== null) {
        cyc.textContent = String(epoch);
    }
}

async function saveRegistrationLobbyName() {
    const input = document.getElementById('registration-lobby-name-input');
    const messageDiv = document.getElementById('lobby-name-message');
    const lobby_name = input ? input.value.trim() : '';
    try {
        messageDiv.innerHTML = '<span class="admin-msg-success">Saving...</span>';
        const response = await fetch('/api/admin/set-registration-lobby-name', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ lobby_name: lobby_name }),
        });
        const data = await response.json();
        if (!response.ok) {
            messageDiv.innerHTML = '<span class="admin-msg-error">Failed: ' + (data.detail || data.message || response.status) + '</span>';
            return;
        }
        if (data.success) {
            syncRegistrationLobbyNameUI(data.registration_lobby_name);
            syncOpsStripLobbyCycle(data.registration_lobby_name, undefined);
            messageDiv.innerHTML = '<span class="admin-msg-success">✓ Saved</span>';
            setTimeout(() => { messageDiv.innerHTML = ''; }, 3000);
        } else {
            messageDiv.innerHTML = '<span class="admin-msg-error">Failed</span>';
        }
    } catch (error) {
        console.error('Error:', error);
        messageDiv.innerHTML = '<span class="admin-msg-error">Request failed</span>';
    }
}

async function resetRegistrationLobby() {
    if (!confirm('Open the next registration lobby? The public countdown will reset and players can sign up again for this new cycle. This does not delete existing entries.')) {
        return;
    }
    const messageDiv = document.getElementById('reset-lobby-message');
    const nameInput = document.getElementById('registration-lobby-name-input');
    const lobbyName = nameInput ? nameInput.value.trim() : '';
    try {
        messageDiv.innerHTML = '<span class="admin-msg-success">Updating...</span>';
        const response = await fetch('/api/admin/reset-registration-lobby', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(lobbyName ? { lobby_name: lobbyName } : {}),
        });
        const data = await response.json();
        if (!response.ok) {
            messageDiv.innerHTML = '<span class="admin-msg-error">Failed: ' + (data.detail || data.message || response.status) + '</span>';
            return;
        }
        if (data.success) {
            messageDiv.innerHTML = '<span class="admin-msg-success">✓ ' + (data.message || 'Lobby cycle updated') + '</span>';
            const epochEl = document.getElementById('registration-lobby-epoch');
            const regEl = document.getElementById('current-cycle-registrations');
            const groupEl = document.getElementById('current-cycle-group');
            const remEl = document.getElementById('current-cycle-remaining');
            if (epochEl) epochEl.textContent = data.registration_lobby_epoch;
            if (regEl) regEl.textContent = data.current_cycle_registrations;
            if (groupEl) groupEl.textContent = data.current_cycle_group_number;
            if (remEl) remEl.textContent = data.current_cycle_remaining_in_group;
            if (data.registration_lobby_name !== undefined) {
                syncRegistrationLobbyNameUI(data.registration_lobby_name);
            }
            syncOpsStripLobbyCycle(data.registration_lobby_name, data.registration_lobby_epoch);
            setTimeout(() => { messageDiv.innerHTML = ''; }, 5000);
        } else {
            messageDiv.innerHTML = '<span class="admin-msg-error">Failed: ' + (data.detail || data.message || 'Unknown error') + '</span>';
        }
    } catch (error) {
        console.error('Error:', error);
        messageDiv.innerHTML = '<span class="admin-msg-error">Request failed</span>';
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

async function deactivateAdminUser(adminUserId) {
    if (!confirm('Remove this admin user? This will deactivate their login.')) {
        return;
    }

    try {
        const response = await fetch('/api/admin/deactivate-admin-user', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ admin_user_id: adminUserId })
        });

        const data = await response.json();
        if (data.success) {
            // Refresh admin users list
            loadAdminUsers();
        } else {
            alert('Failed to remove admin: ' + (data.message || data.detail || 'Unknown error'));
        }
    } catch (e) {
        console.error('Error deactivating admin:', e);
        alert('An error occurred while removing the admin user.');
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
                        <div class="admin-user-info">
                            <strong>${admin.username}</strong>
                            <span>${admin.email || 'No email'}</span>
                            <span style="display:block;margin-top:4px;font-size:11px;">${new Date(admin.created_at).toLocaleDateString()}</span>
                        </div>
                        <div class="admin-user-actions">
                            ${statusBadge}
                            <button type="button" class="admin-btn admin-btn-sm admin-btn-danger" style="margin-left: 10px;" onclick="deactivateAdminUser('${admin.id}')">Remove</button>
                        </div>
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

function syncEntryFeeAutoUi() {
    const auto = document.getElementById('entry-fee-auto');
    const ngn = document.getElementById('entry-fee-ngn');
    if (!auto || !ngn) return;
    ngn.disabled = auto.checked;
}

function applyRuntimeSettingsToForm(data) {
    if (!data || !data.success) return;
    const auto = document.getElementById('entry-fee-auto');
    const ngn = document.getElementById('entry-fee-ngn');
    const lobby = document.getElementById('lobby-group-size-input');
    const mile = document.getElementById('registration-milestone-input');
    const perKill = document.getElementById('per-kill-usd-input');
    if (auto) auto.checked = !!data.entry_fee_auto;
    if (ngn) {
        ngn.value = data.entry_fee_ngn_override != null && data.entry_fee_ngn_override !== undefined
            ? String(Math.round(Number(data.entry_fee_ngn_override)))
            : '';
    }
    if (lobby) lobby.value = data.lobby_group_size;
    if (mile) mile.value = data.registration_milestone;
    if (perKill) perKill.value = data.per_kill_value_usd;
    syncEntryFeeAutoUi();
    syncOpsStripFromRuntime(data);
}

function syncOpsStripFromRuntime(data) {
    if (!data || !data.success) return;
    const fee = document.getElementById('admin-ops-strip-fee');
    const grp = document.getElementById('admin-ops-strip-group');
    if (fee != null && data.entry_fee_effective_ngn != null && data.entry_fee_effective_ngn !== undefined) {
        fee.textContent = '₦' + String(Math.round(Number(data.entry_fee_effective_ngn)));
    }
    if (grp != null && data.lobby_group_size != null && data.lobby_group_size !== undefined) {
        grp.textContent = String(data.lobby_group_size);
    }
}

async function saveRuntimeSettings() {
    const msg = document.getElementById('runtime-settings-message');
    const auto = document.getElementById('entry-fee-auto');
    const ngn = document.getElementById('entry-fee-ngn');
    const lobby = document.getElementById('lobby-group-size-input');
    const mile = document.getElementById('registration-milestone-input');
    const perKill = document.getElementById('per-kill-usd-input');
    if (!msg || !auto || !ngn || !lobby || !mile || !perKill) return;

    const body = {};
    if (auto.checked) {
        body.entry_fee_auto = true;
    } else {
        const v = parseFloat(ngn.value);
        if (!Number.isFinite(v) || v < 1) {
            msg.innerHTML = '<span class="admin-msg-error">Enter a valid entry fee in NGN or enable automatic fee.</span>';
            return;
        }
        body.entry_fee_ngn = v;
    }

    const lg = parseInt(lobby.value, 10);
    if (!Number.isFinite(lg) || lg < 1) {
        msg.innerHTML = '<span class="admin-msg-error">Players per group must be at least 1.</span>';
        return;
    }
    body.lobby_group_size = lg;

    const ms = parseInt(mile.value, 10);
    if (!Number.isFinite(ms) || ms < 1) {
        msg.innerHTML = '<span class="admin-msg-error">Milestone must be at least 1.</span>';
        return;
    }
    body.registration_milestone = ms;

    const pk = parseFloat(perKill.value);
    if (!Number.isFinite(pk) || pk <= 0) {
        msg.innerHTML = '<span class="admin-msg-error">Per-kill USD must be greater than 0.</span>';
        return;
    }
    body.per_kill_value_usd = pk;

    const saveBtn = document.getElementById('save-runtime-settings-btn');
    try {
        if (saveBtn) saveBtn.disabled = true;
        msg.innerHTML = '<span class="admin-msg-success">Saving...</span>';
        const res = await fetch('/api/admin/runtime-settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        const data = await res.json();
        if (!res.ok) {
            msg.innerHTML = '<span class="admin-msg-error">Failed: ' + (data.detail || res.status) + '</span>';
            return;
        }
        applyRuntimeSettingsToForm(data);
        msg.innerHTML = '<span class="admin-msg-success">✓ Saved</span>';
        setTimeout(function() { msg.innerHTML = ''; }, 4000);
    } catch (e) {
        msg.innerHTML = '<span class="admin-msg-error">Request failed</span>';
    } finally {
        if (saveBtn) saveBtn.disabled = false;
    }
}

async function clearRuntimeSettingField(which) {
    const msg = document.getElementById('runtime-settings-message');
    const body = {};
    if (which === 'lobby_group') body.clear_lobby_group_size = true;
    else if (which === 'milestone') body.clear_registration_milestone = true;
    else if (which === 'per_kill') body.clear_per_kill_value = true;
    else return;
    try {
        const res = await fetch('/api/admin/runtime-settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        const data = await res.json();
        if (!res.ok) {
            if (msg) msg.innerHTML = '<span class="admin-msg-error">Failed</span>';
            return;
        }
        applyRuntimeSettingsToForm(data);
        if (msg) {
            msg.innerHTML = '<span class="admin-msg-success">✓ Reset to env default</span>';
            setTimeout(function() { msg.innerHTML = ''; }, 3000);
        }
    } catch (e) {
        if (msg) msg.innerHTML = '<span class="admin-msg-error">Request failed</span>';
    }
}

function initEntriesTableFilter() {
    const input = document.getElementById('entries-search-input');
    const table = document.getElementById('admin-entries-table');
    const hint = document.getElementById('entries-filter-hint');
    if (!input || !table) return;
    const tbody = table.querySelector('tbody');
    if (!tbody) return;
    const rows = Array.from(tbody.querySelectorAll('tr'));

    function apply() {
        const raw = (input.value || '').trim().toLowerCase();
        const q = raw.replace(/\s+/g, ' ');
        let visible = 0;
        for (let i = 0; i < rows.length; i++) {
            const row = rows[i];
            const hay = (row.getAttribute('data-admin-search') || '');
            const ok = !q || hay.indexOf(q) !== -1;
            row.style.display = ok ? '' : 'none';
            if (ok) visible += 1;
        }
        if (hint) {
            if (!q) {
                hint.textContent = rows.length ? rows.length + ' entries' : 'No entries';
            } else {
                hint.textContent = visible + ' shown' + (visible !== rows.length ? ' of ' + rows.length : '');
            }
        }
    }

    input.addEventListener('input', apply);
    input.addEventListener('search', apply);
    apply();
}

// Initialize auto-refresh on page load
document.addEventListener('DOMContentLoaded', function() {
    initEntriesTableFilter();

    const efa = document.getElementById('entry-fee-auto');
    if (efa) {
        efa.addEventListener('change', syncEntryFeeAutoUi);
        syncEntryFeeAutoUi();
    }

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

