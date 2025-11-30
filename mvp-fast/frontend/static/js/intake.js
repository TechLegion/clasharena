document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('intakeForm');
    const submitBtn = document.getElementById('submitBtn');
    const errorMsg = document.getElementById('errorMsg');
    const successMsg = document.getElementById('successMsg');
    
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
                    'Content-Type': 'application/json'
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

