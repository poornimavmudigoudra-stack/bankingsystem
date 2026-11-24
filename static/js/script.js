/**
 * Apex National Bank - Client-Side Interactive Scripts
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Auto-dismiss Flash Alerts
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        // Allow close button click
        const closeBtn = alert.querySelector('.alert-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                alert.style.opacity = '0';
                alert.style.transform = 'translateY(-8px)';
                setTimeout(() => alert.remove(), 250);
            });
        }

        // Auto fade out after 6 seconds
        setTimeout(() => {
            if (alert && alert.parentElement) {
                alert.style.opacity = '0';
                alert.style.transform = 'translateY(-8px)';
                setTimeout(() => alert.remove(), 300);
            }
        }, 6000);
    });

    // 2. Copy Account Number to Clipboard
    const copyButtons = document.querySelectorAll('[data-copy]');
    copyButtons.forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            const textToCopy = btn.getAttribute('data-copy');
            try {
                await navigator.clipboard.writeText(textToCopy);
                const originalText = btn.innerHTML;
                btn.innerHTML = '<span>✓ Copied!</span>';
                btn.classList.add('btn-success');
                setTimeout(() => {
                    btn.innerHTML = originalText;
                    btn.classList.remove('btn-success');
                }, 2000);
            } catch (err) {
                console.error('Failed to copy: ', err);
            }
        });
    });

    // 3. Quick Confirmation for Fund Transfers and Critical Actions
    const transferForms = document.querySelectorAll('form[data-confirm-transfer]');
    transferForms.forEach(form => {
        form.addEventListener('submit', (e) => {
            const recipientInput = form.querySelector('[name="recipient_account"]');
            const amountInput = form.querySelector('[name="amount"]');
            const recipient = recipientInput ? recipientInput.value.trim() : '';
            const amount = amountInput ? parseFloat(amountInput.value) : 0;

            if (amount > 0 && recipient) {
                const confirmed = window.confirm(
                    `Please confirm your transaction:\n\n` +
                    `Amount: $${amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}\n` +
                    `Recipient Account: ${recipient}\n\n` +
                    `Do you wish to authorize this transfer immediately?`
                );
                if (!confirmed) {
                    e.preventDefault();
                }
            }
        });
    });

    // 4. Live Table Search Filter (Dashboard, Admin Customer list, Transactions)
    const searchInput = document.getElementById('tableSearchInput');
    const tableToFilter = document.getElementById('searchableTable');
    if (searchInput && tableToFilter) {
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase().trim();
            const rows = tableToFilter.querySelectorAll('tbody tr');

            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                if (text.includes(query)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }

    // 5. Password Visibility Toggle
    const togglePasswordButtons = document.querySelectorAll('[data-toggle-password]');
    togglePasswordButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetId = btn.getAttribute('data-toggle-password');
            const input = document.getElementById(targetId);
            if (input) {
                if (input.type === 'password') {
                    input.type = 'text';
                    btn.textContent = 'Hide';
                } else {
                    input.type = 'password';
                    btn.textContent = 'Show';
                }
            }
        });
    });

    // 6. Number formatting for amount input
    const currencyInputs = document.querySelectorAll('input[type="number"][step="0.01"]');
    currencyInputs.forEach(input => {
        input.addEventListener('blur', () => {
            if (input.value && !isNaN(input.value)) {
                input.value = parseFloat(input.value).toFixed(2);
            }
        });
    });
});
