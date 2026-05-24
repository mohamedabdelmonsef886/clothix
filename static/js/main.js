// Products Page Functionality
document.addEventListener('DOMContentLoaded', function() {
    initProductsPage();
});

function initProductsPage() {
    // Sort functionality
    const sortSelect = document.getElementById('sortSelect');
    if (sortSelect) {
        sortSelect.addEventListener('change', function() {
            const sortValue = this.value;
            const currentUrl = new URL(window.location.href);
            currentUrl.searchParams.set('sort', sortValue);
            currentUrl.searchParams.set('page', '1');
            window.location.href = currentUrl.toString();
        });
    }
    
    // Add to cart functionality
    const addToCartButtons = document.querySelectorAll('.add-to-cart');
    addToCartButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            const productId = this.dataset.id;
            addToCart(productId);
        });
    });
    
    // Quick view functionality
    const quickViewButtons = document.querySelectorAll('.quick-view');
    quickViewButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (this.tagName === 'A') return;
            e.preventDefault();
            const productCard = this.closest('.product-card');
            const productName = productCard.querySelector('h3').innerText;
            const productPrice = productCard.querySelector('.current-price').innerText;
            showNotification(`${productName} added to cart!`);
        });
    });
}

function addToCart(productId) {
    // Update cart count in navbar
    const cartCount = document.querySelector('.cart-count');
    let currentCount = parseInt(cartCount.innerText);
    cartCount.innerText = currentCount + 1;
    
    // Show notification
    showNotification('Product added to cart!');
    
    // You can add AJAX call here to save to session/cart
    console.log(`Product ${productId} added to cart`);
}

function showNotification(message) {
    // Remove existing notification
    const existingNotification = document.querySelector('.notification');
    if (existingNotification) {
        existingNotification.remove();
    }
    
    // Create notification
    const notification = document.createElement('div');
    notification.className = 'notification';
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas fa-check-circle"></i>
            <span>${message}</span>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Show notification
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
    
    // Hide and remove after 3 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}

// Add notification styles dynamically if not already in CSS
if (!document.querySelector('#notification-styles')) {
    const notificationStyles = document.createElement('style');
    notificationStyles.id = 'notification-styles';
    notificationStyles.textContent = `
        .notification {
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 10000;
            opacity: 0;
            transform: translateX(100%);
            transition: all 0.3s ease;
        }
        
        .notification.show {
            opacity: 1;
            transform: translateX(0);
        }
        
        .notification-content {
            background: var(--primary, #000);
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 50px;
            display: flex;
            align-items: center;
            gap: 0.75rem;
            box-shadow: 0 5px 20px rgba(0,0,0,0.2);
        }
        
        .notification-content i {
            font-size: 1.2rem;
        }
    `;
    document.head.appendChild(notificationStyles);
}

// popup
// Quick View Modal Functionality
document.addEventListener('DOMContentLoaded', function() {
    initQuickView();
});

function initQuickView() {
    const modal = document.getElementById('quickViewModal');
    const modalContent = document.getElementById('quickViewContent');
    const closeBtn = document.querySelector('.modal-close');
    
    // Get all Quick View buttons
    const quickViewBtns = document.querySelectorAll('.quick-view');
    
    quickViewBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const productCard = this.closest('.product-card');
            const productId = this.getAttribute('data-id') || productCard.querySelector('.add-to-cart')?.getAttribute('data-id');
            
            if (productId) {
                loadProductQuickView(productId);
            } else {
                // If no product ID, get info from the card
                const productName = productCard.querySelector('h3')?.innerText || 'Product';
                const productPrice = productCard.querySelector('.current-price')?.innerText || '$0';
                const productImage = productCard.querySelector('img')?.src || '';
                const productDiscount = productCard.querySelector('.product-badge.sale')?.innerText || '';
                
                showQuickViewFromCard({
                    id: productId,
                    name: productName,
                    price: productPrice,
                    image: productImage,
                    discount: productDiscount
                });
            }
        });
    });
    
    // Close modal when clicking on X
    if (closeBtn) {
        closeBtn.addEventListener('click', function() {
            modal.style.display = 'none';
        });
    }
    
    // Close modal when clicking outside
    window.addEventListener('click', function(e) {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });
}

function loadProductQuickView(productId) {
    const modal = document.getElementById('quickViewModal');
    const modalContent = document.getElementById('quickViewContent');
    
    // Show loading
    modalContent.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i> Loading product details...</div>';
    modal.style.display = 'block';
    
    // In a real application, you would make an AJAX call here
    fetch(`/products/quick-view/${productId}/`)
    .then(response => response.json())
    .then(data => {
        displayQuickView(data);
    })
    .catch(error => {
        console.error('Error:', error);
        modalContent.innerHTML = '<div class="loading-spinner">Error loading product. Please try again.</div>';
    });
}

function showQuickViewFromCard(productData) {
    const modal = document.getElementById('quickViewModal');
    const modalContent = document.getElementById('quickViewContent');
    
    displayQuickView({
        id: productData.id,
        name: productData.name,
        price: productData.price,
        image: productData.image,
        description: 'High quality product from Clothix collection.',
        stock: 'In Stock'
    });
    
    modal.style.display = 'block';
}

function displayQuickView(product) {
    const modalContent = document.getElementById('quickViewContent');
    
    const discountHtml = product.discount ? `<span class="quick-view-discount">-${product.discount}</span>` : '';
    const originalPriceHtml = product.original_price ? `<span class="quick-view-original-price">${product.original_price}</span>` : '';
    
       // Use slug instead of ID 
    const detailUrl = product.slug ? `/products/${product.slug}/` : `/products/${product.id}/`;
    modalContent.innerHTML = `
    <div class="quick-view-layout">
        <div class="quick-view-image">
            <img src="${product.image}" alt="${product.name}">
        </div>
        <div class="quick-view-details">
            <h2>${product.name}</h2>
            <div class="quick-view-price">
                ${product.price}
                ${originalPriceHtml}
                ${discountHtml}
            </div>
            <div class="quick-view-meta">
                <p><strong>Category:</strong> ${product.category || 'Fashion'}</p>
                <p><strong>Availability:</strong> <span style="color: ${product.stock === 'In Stock' ? '#28a745' : '#dc3545'};">${product.stock || 'In Stock'}</span></p>
            </div>
            <div class="quick-view-description">
                <p>${product.description || 'Premium quality product from Clothix. Designed for comfort and style.'}</p>
            </div>
            <div class="quick-view-actions">
                <button class="add-to-cart-modal" data-id="${product.id}">
                    <i class="fas fa-shopping-bag"></i> Add to Cart
                </button>

                <a href="${detailUrl}" class="view-details-btn">
                    View Full Details
                </a>
            </div>
        </div>
    </div>
`;
    
    // Add event listener for add to cart button in modal
    const addToCartBtn = modalContent.querySelector('.add-to-cart-modal');
    if (addToCartBtn) {
        addToCartBtn.addEventListener('click', function(e) {
            e.preventDefault();
            addToCart(product.id);
            const modal = document.getElementById('quickViewModal');
            if (modal) {
                modal.style.display = 'none';
            }
            showNotification(`${product.name} added to cart!`);
        });
    }
}
//  add to cart

// Get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Show notification
function showNotification(message, type = 'success') {
    const existingNotification = document.querySelector('.notification');
    if (existingNotification) {
        existingNotification.remove();
    }
    
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'}"></i>
            <span>${message}</span>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
    
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}

// Add to cart function
function addToCart(productId, quantity = 1, size = '', color = '') {
    fetch('/products/cart/add/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: `product_id=${productId}&quantity=${quantity}&size=${size}&color=${color}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.total_items !== undefined) {
            const cartCount = document.querySelector('.cart-count');
            if (cartCount) { 
                // Add bump animation
                cartCount.classList.add('bump');
                setTimeout(() => {
                cartCount.classList.remove('bump');
                }, 300);
                // Update count
                cartCount.innerText = data.total_items;
            }
            showNotification(data.message || 'Product added to cart!');
        } else if (data.error) {
            showNotification(data.error, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error adding to cart', 'error');
    });
}

// Products Page Functionality
function initProductsPage() {
    const sortSelect = document.getElementById('sortSelect');
    if (sortSelect) {
        sortSelect.addEventListener('change', function() {
            const sortValue = this.value;
            const currentUrl = new URL(window.location.href);
            currentUrl.searchParams.set('sort', sortValue);
            currentUrl.searchParams.set('page', '1');
            window.location.href = currentUrl.toString();
        });
    }
}

// Quick View Modal Functionality
function initQuickView() {
    const modal = document.getElementById('quickViewModal');
    const closeBtn = document.querySelector('.modal-close');
    
    if (!modal) return;
    
    const quickViewBtns = document.querySelectorAll('.quick-view');
    
    quickViewBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const productId = this.getAttribute('data-id');
            if (productId) {
                loadProductQuickView(productId);
            }
        });
    });
    
    if (closeBtn) {
        closeBtn.addEventListener('click', function() {
            modal.style.display = 'none';
        });
    }
    
    window.addEventListener('click', function(e) {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });
}

function loadProductQuickView(productId) {
    const modal = document.getElementById('quickViewModal');
    const modalContent = document.getElementById('quickViewContent');
    
    if (!modal || !modalContent) return;
    
    modalContent.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i> Loading product details...</div>';
    modal.style.display = 'block';
    
    fetch(`/products/quick-view/${productId}/`)
        .then(response => response.json())
        .then(data => {
            displayQuickView(data);
        })
        .catch(error => {
            console.error('Error:', error);
            modalContent.innerHTML = '<div class="loading-spinner">Error loading product. Please try again.</div>';
        });
}

function displayQuickView(product) {
    const modalContent = document.getElementById('quickViewContent');
    
    const discountHtml = product.discount ? `<span class="quick-view-discount">-${product.discount}</span>` : '';
    const originalPriceHtml = product.original_price ? `<span class="quick-view-original-price">${product.original_price}</span>` : '';
    const detailUrl = product.slug ? `/products/${product.slug}/` : `/products/${product.id}/`;
    
    modalContent.innerHTML = `
        <div class="quick-view-layout">
            <div class="quick-view-image">
                <img src="${product.image}" alt="${product.name}">
            </div>
            <div class="quick-view-details">
                <h2>${product.name}</h2>
                <div class="quick-view-price">
                    ${product.price}
                    ${originalPriceHtml}
                    ${discountHtml}
                </div>
                <div class="quick-view-meta">
                    <p><strong>Category:</strong> ${product.category || 'Fashion'}</p>
                    <p><strong>Availability:</strong> <span style="color: ${product.stock === 'In Stock' ? '#28a745' : '#dc3545'};">${product.stock || 'In Stock'}</span></p>
                </div>
                <div class="quick-view-description">
                    <p>${product.description || 'Premium quality product from Clothix.'}</p>
                </div>
                <div class="quick-view-actions">
                    <button class="add-to-cart-modal" data-id="${product.id}">
                        <i class="fas fa-shopping-bag"></i> Add to Cart
                    </button>
                    <a href="${detailUrl}" class="view-details-btn">
                        View Full Details
                    </a>
                </div>
            </div>
        </div>
    `;
    
    const addToCartBtn = modalContent.querySelector('.add-to-cart-modal');
    if (addToCartBtn) {
        addToCartBtn.addEventListener('click', function(e) {
            e.preventDefault();
            addToCart(product.id);
            const modal = document.getElementById('quickViewModal');
            if (modal) {
                modal.style.display = 'none';
            }
            showNotification(`${product.name} added to cart!`);
        });
    }
}

// Initialize everything when page loads
document.addEventListener('DOMContentLoaded', function() {
    initProductsPage();
    initQuickView();
    
    // Add to cart buttons in products grid
    const addToCartButtons = document.querySelectorAll('.add-to-cart');
    addToCartButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            const productId = this.getAttribute('data-id');
            if (productId) {
                addToCart(productId);
            }
        });
    });
    
    // Add to cart button in product detail page
    const addToCartDetail = document.querySelector('.add-to-cart-detail');
    if (addToCartDetail) {
        addToCartDetail.addEventListener('click', function() {
            const productId = this.getAttribute('data-id');
            const quantityInput = document.getElementById('quantity');
            const quantity = quantityInput ? parseInt(quantityInput.value) : 1;
            const selectedSize = document.querySelector('.size-option.active');
            const size = selectedSize ? selectedSize.getAttribute('data-size') : '';
            
            if (productId) {
                addToCart(productId, quantity, size);
            }
        });
    }
});

// Add notification styles
if (!document.querySelector('#notification-styles')) {
    const notificationStyles = document.createElement('style');
    notificationStyles.id = 'notification-styles';
    notificationStyles.textContent = `
        .notification {
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 10000;
            opacity: 0;
            transform: translateX(100%);
            transition: all 0.3s ease;
        }
        .notification.show {
            opacity: 1;
            transform: translateX(0);
        }
        .notification-content {
            background: var(--primary-dark, #000);
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 50px;
            display: flex;
            align-items: center;
            gap: 0.75rem;
            box-shadow: 0 5px 20px rgba(0,0,0,0.2);
        }
        .notification.success .notification-content {
            background: #28a745;
        }
        .notification.error .notification-content {
            background: #dc3545;
        }
        .notification-content i {
            font-size: 1.2rem;
        }
    `;
    document.head.appendChild(notificationStyles);
}