document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('intakeForm');
    const submitBtn = document.getElementById('submitBtn');
    const errorMsg = document.getElementById('errorMsg');
    const successMsg = document.getElementById('successMsg');

    const groupRemainingEl = document.getElementById('group-remaining');
    const spotsRestEl = document.getElementById('spots-rest');

    function applySpotsRemaining(raw) {
        const num = Math.max(0, Number(raw));
        if (!Number.isFinite(num)) return;
        if (groupRemainingEl) groupRemainingEl.textContent = String(num);
        if (spotsRestEl) {
            spotsRestEl.textContent =
                (num === 1 ? ' spot' : ' spots') + ' left for the current lobby';
        }
    }

    async function updateGroupCountdown() {
        if (!groupRemainingEl) return;
        try {
            const res = await fetch('/api/registration-group-status', {
                method: 'GET',
                credentials: 'same-origin',
                cache: 'no-store',
                headers: { Accept: 'application/json' },
            });
            if (!res.ok) return;
            const data = await res.json();
            if (data && data.success && data.remaining_in_group != null) {
                applySpotsRemaining(data.remaining_in_group);
            }
        } catch (e) {
            console.error('Failed to fetch group countdown:', e);
        }
    }

    updateGroupCountdown();
    setInterval(updateGroupCountdown, 8000);

    window.addEventListener('pageshow', function(e) {
        if (e && e.persisted) {
            updateGroupCountdown();
        }
    });

    document.addEventListener('visibilitychange', function() {
        if (!document.hidden) updateGroupCountdown();
    });
    
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        submitBtn.disabled = true;
        errorMsg.style.display = 'none';
        successMsg.style.display = 'none';
        
        const formData = {
            payment_reference: document.getElementById('paymentReference').value.trim(),
            codm_id: document.getElementById('codm_id').value.trim(),
            contact_phone: document.getElementById('contact_phone').value.trim(),
            contact_email: document.getElementById('contact_email').value.trim(),
            region: document.getElementById('region').value.trim(),
            bank_name: document.getElementById('bank_name').value.trim(),
            account_number: document.getElementById('account_number').value.trim(),
            account_name: document.getElementById('account_name').value.trim()
        };
        
        // Log form data for debugging
        console.log('Submitting form data:', formData);
        
        try {
            const response = await fetch('/api/submit-intake', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json; charset=utf-8',
                    Accept: 'application/json; charset=utf-8',
                },
                body: JSON.stringify(formData)
            });
            
            const data = await response.json();
            console.log('Response:', response.status, data);
            
            if (!response.ok) {
                // Handle validation errors
                let errorText = data.message || 'An error occurred. Please try again.';
                if (data.errors && Array.isArray(data.errors)) {
                    errorText = 'Validation errors:\n' + data.errors.join('\n');
                } else if (data.detail) {
                    errorText = data.detail;
                }
                errorMsg.textContent = errorText;
                errorMsg.style.display = 'block';
                submitBtn.disabled = false;
                console.error('Error response:', data);
                return;
            }
            
            if (data.success) {
                successMsg.textContent = 'Registration successful! Redirecting...';
                successMsg.style.display = 'block';
                setTimeout(() => {
                    window.location.href = data.redirect_url;
                }, 1500);
            } else {
                errorMsg.textContent = data.message || 'An error occurred. Please try again.';
                errorMsg.style.display = 'block';
                submitBtn.disabled = false;
            }
        } catch (error) {
            console.error('Error:', error);
            errorMsg.textContent = 'An error occurred. Please try again.';
            errorMsg.style.display = 'block';
            submitBtn.disabled = false;
        }
    });
});

