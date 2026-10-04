/**
 * School E-Commerce Marketplace - Client Interactions
 * Handles up to 3 image file preview, dynamic AJAX cart additions,
 * interactive image gallery, toast alerts, and direct WhatsApp links.
 */

document.addEventListener('DOMContentLoaded', () => {
    initImageUploadPreview();
    initAjaxAddToCart();
    initProductGallery();
    initAutoDismissAlerts();
});

/**
 * Image Upload Preview for up to 3 images in "Sell Your Product"
 */
function initImageUploadPreview() {
    const fileInput = document.getElementById('product-images-input');
    const previewGrid = document.getElementById('image-preview-grid');
    if (!fileInput || !previewGrid) return;

    fileInput.addEventListener('change', (e) => {
        const files = Array.from(e.target.files);
        
        if (files.length > 3) {
            showToast("⚠️ Note: Only the first 3 images will be uploaded.", "warning");
        }

        const validFiles = files.slice(0, 3);
        
        // Reset preview slots
        const slots = previewGrid.querySelectorAll('.preview-slot');
        slots.forEach((slot, index) => {
            slot.innerHTML = `<span class="preview-slot-empty">Image ${index + 1}</span>`;
        });

        validFiles.forEach((file, index) => {
            if (!file.type.startsWith('image/')) return;
            const reader = new FileReader();
            reader.onload = (event) => {
                if (slots[index]) {
                    slots[index].innerHTML = `
                        <img src="${event.target.result}" alt="Preview ${index + 1}">
                        <div style="position:absolute; bottom:4px; right:4px; background:rgba(0,0,0,0.6); color:white; font-size:10px; padding:2px 6px; border-radius:4px;">
                            Slot ${index + 1}
                        </div>
                    `;
                }
            };
            reader.readAsDataURL(file);
        });
    });
}

/**
 * Dynamic AJAX Add to Cart with real-time badge update and toast alert
 */
function initAjaxAddToCart() {
    document.querySelectorAll('.ajax-add-cart-form').forEach(form => {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const url = form.getAttribute('action');
            const submitBtn = form.querySelector('button[type="submit"]');
            const originalContent = submitBtn.innerHTML;

            try {
                submitBtn.disabled = true;
                submitBtn.innerHTML = `
                    <svg class="spinner" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="animation: spin 1s linear infinite;">
                        <circle cx="12" cy="12" r="10" stroke-opacity="0.25"></circle>
                        <path d="M12 2a10 10 0 0 1 10 10"></path>
                    </svg>
                    Adding...
                `;

                const res = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'Content-Type': 'application/json'
                    }
                });

                const data = await res.json();
                if (data.success) {
                    // Update cart badge in navbar
                    const badge = document.getElementById('navbar-cart-badge');
                    if (badge) {
                        badge.textContent = data.cart_count;
                        badge.style.display = data.cart_count > 0 ? 'flex' : 'none';
                        badge.classList.remove('badgePop');
                        void badge.offsetWidth; // trigger reflow
                        badge.classList.add('badgePop');
                    }
                    showToast(`🛍️ ${data.product_title || 'Item'} added to cart!`, 'success');
                } else {
                    showToast(data.message || 'Could not add to cart.', 'error');
                }
            } catch (err) {
                console.error("Cart error:", err);
                // Fallback to normal form submit if fetch fails
                form.submit();
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalContent;
            }
        });
    });
}

/**
 * Image Gallery switcher on Product Detail page
 */
function initProductGallery() {
    const mainImg = document.getElementById('main-gallery-image');
    const thumbs = document.querySelectorAll('.gallery-thumb');
    if (!mainImg || !thumbs.length) return;

    thumbs.forEach(thumb => {
        thumb.addEventListener('click', () => {
            thumbs.forEach(t => t.classList.remove('active'));
            thumb.classList.add('active');
            const newSrc = thumb.getAttribute('data-full-img');
            if (newSrc) {
                mainImg.src = newSrc;
            }
        });
    });
}

/**
 * Toast Notification system
 */
function showToast(message, type = 'success') {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = 'toast';
    if (type === 'error') {
        toast.style.borderLeftColor = 'var(--danger)';
    } else if (type === 'warning') {
        toast.style.borderLeftColor = 'var(--warning)';
    }

    toast.innerHTML = `
        <div style="display:flex; align-items:center; gap:8px;">
            <span>${message}</span>
        </div>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(15px)';
        setTimeout(() => toast.remove(), 400);
    }, 3200);
}

/**
 * Auto-dismiss Flask flash messages after 4 seconds
 */
function initAutoDismissAlerts() {
    const alerts = document.querySelectorAll('.flask-alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-10px)';
            setTimeout(() => alert.remove(), 400);
        }, 4000);
    });
}
