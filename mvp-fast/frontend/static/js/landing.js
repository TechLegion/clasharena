document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('entryForm');
    const enterBtn = document.getElementById('enterBtn');
    const loading = document.getElementById('loading');
    const errorMsg = document.getElementById('errorMsg');
    const emailInput = document.getElementById('email');
    
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

