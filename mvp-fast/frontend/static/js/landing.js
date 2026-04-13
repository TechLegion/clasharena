document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('entryForm');
    const enterBtn = document.getElementById('enterBtn');
    const loading = document.getElementById('loading');
    const errorMsg = document.getElementById('errorMsg');
    const emailInput = document.getElementById('email');
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
            if (!res.ok) {
                console.error('registration-group-status HTTP', res.status);
                return;
            }
            const data = await res.json();

            if (data && data.success && data.remaining_in_group != null) {
                applySpotsRemaining(data.remaining_in_group);
            }
        } catch (e) {
            console.error('Failed to fetch group countdown:', e);
        }
    }

    // Update immediately, then poll (was 15s; faster refresh feels live).
    updateGroupCountdown();
    setInterval(updateGroupCountdown, 8000);

    // Handle BFCache/back-navigation: the page might not reload,
    // so we re-fetch the countdown when the page is shown again.
    window.addEventListener('pageshow', function(e) {
        if (e && e.persisted) {
            updateGroupCountdown();
        }
    });

    // Extra safety: refresh when user returns to the tab.
    document.addEventListener('visibilitychange', function() {
        if (!document.hidden) updateGroupCountdown();
    });
    
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const email = emailInput.value.trim();
        
        if (!email) {
            errorMsg.textContent = 'Please enter your email address';
            errorMsg.style.display = 'block';
            return;
        }
        
        // Basic email validation
        if (!email.includes('@') || !email.includes('.')) {
            errorMsg.textContent = 'Please enter a valid email address';
            errorMsg.style.display = 'block';
            return;
        }

        var termsBox = document.getElementById('termsCheckbox');
        if (termsBox && !termsBox.checked) {
            errorMsg.textContent = 'You must agree to the Terms & Conditions before entering.';
            errorMsg.style.display = 'block';
            return;
        }
        
        errorMsg.style.display = 'none';
        await initiatePayment(email);
    });
    
    async function initiatePayment(email) {
        enterBtn.disabled = true;
        loading.style.display = 'block';
        
        try {
            const formData = new FormData();
            formData.append('email', email);
            
            const response = await fetch('/api/initiate-payment', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Check if already registered or payment completed
                if (data.already_registered || data.payment_completed) {
                    // Hide loading state first
                    loading.style.display = 'none';
                    enterBtn.disabled = false;
                    
                    // Redirect to appropriate page
                    if (data.redirect_url) {
                        // Small delay to ensure UI updates before redirect
                        setTimeout(() => {
                            window.location.href = data.redirect_url;
                        }, 100);
                    } else {
                        errorMsg.textContent = data.message || 'You have already registered';
                        errorMsg.style.display = 'block';
                    }
                } else if (data.checkout_url) {
                    // Hide loading state before redirecting to payment
                    loading.style.display = 'none';
                    enterBtn.disabled = false;
                    
                    // Redirect to payment gateway
                    setTimeout(() => {
                        window.location.href = data.checkout_url;
                    }, 100);
                } else {
                    errorMsg.textContent = 'Invalid response from server';
                    errorMsg.style.display = 'block';
                    enterBtn.disabled = false;
                    loading.style.display = 'none';
                }
            } else {
                errorMsg.textContent = 'Failed to initiate payment: ' + (data.message || 'Unknown error');
                errorMsg.style.display = 'block';
                enterBtn.disabled = false;
                loading.style.display = 'none';
            }
        } catch (error) {
            console.error('Error:', error);
            errorMsg.textContent = 'An error occurred. Please try again.';
            errorMsg.style.display = 'block';
            enterBtn.disabled = false;
            loading.style.display = 'none';
        }
    }
});

