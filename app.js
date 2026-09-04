// Dummy Farm Produce Data (Injected from Farmer WhatsApp Bot updates)
const productsData = [
  {
    id: 'prod_1',
    name: 'Organic Cavendish Bananas',
    pricePerKg: 22,
    minLimitKg: 50,
    farmerName: 'Ramesh Kumar',
    location: 'Mandya, Karnataka',
    image: 'https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?auto=format&fit=crop&q=80&w=600'
  },
  {
    id: 'prod_2',
    name: 'Red Tomatoes (Grade A)',
    pricePerKg: 18,
    minLimitKg: 50,
    farmerName: 'Suresh Patil',
    location: 'Nashik, Maharashtra',
    image: 'https://images.unsplash.com/photo-1592924357228-91a4daadcfea?auto=format&fit=crop&q=80&w=600'
  },
  {
    id: 'prod_3',
    name: 'Fresh Red Onions',
    pricePerKg: 28,
    minLimitKg: 50,
    farmerName: 'Balwinder Singh',
    location: 'Ludhiana, Punjab',
    image: 'https://images.unsplash.com/photo-1618512496248-a07fe83aa8cf?auto=format&fit=crop&q=80&w=600'
  },
  {
    id: 'prod_4',
    name: 'Yukon Gold Potatoes',
    pricePerKg: 20,
    minLimitKg: 50,
    farmerName: 'Venkatesh Rao',
    location: 'Hassan, Karnataka',
    image: 'https://images.unsplash.com/photo-1518977676601-b53f82aba655?auto=format&fit=crop&q=80&w=600'
  }
];

// App State
let cart = {};
let authenticatedUser = null;

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
  renderProducts();
  checkPersistedAuth();
});

// Render Product Cards
function renderProducts() {
  const grid = document.getElementById('products-grid');
  grid.innerHTML = '';

  productsData.forEach(product => {
    const card = document.createElement('div');
    card.className = 'product-card';
    card.innerHTML = `
      <img src="${product.image}" alt="${product.name}" class="product-img" />
      <div class="product-info">
        <div class="product-header">
          <span class="product-title">${product.name}</span>
          <span class="product-price">₹${product.pricePerKg}/kg</span>
        </div>
        <div class="farmer-badge">
          👨‍🌾 <strong>${product.farmerName}</strong> • 📍 ${product.location}
        </div>
        <div class="quantity-control">
          <label for="qty-${product.id}">Order Quantity (Min. ${product.minLimitKg} kg)</label>
          <div class="qty-input-group">
            <input 
              type="number" 
              id="qty-${product.id}" 
              min="0" 
              placeholder="0" 
              oninput="updateCartQuantity('${product.id}', this.value)" 
            />
            <span>kg</span>
          </div>
        </div>
      </div>
    `;
    grid.appendChild(card);
  });
}

// Update Cart Logic with Minimum Bulk Validation
function updateCartQuantity(productId, quantityStr) {
  const qty = parseInt(quantityStr) || 0;
  const product = productsData.find(p => p.id === productId);

  if (qty > 0) {
    cart[productId] = {
      product: product,
      quantity: qty,
      isValid: qty >= product.minLimitKg
    };
  } else {
    delete cart[productId];
  }

  renderCartSummary();
}

// Render Cart Summary
function renderCartSummary() {
  const cartContainer = document.getElementById('cart-items');
  const cartTotalWeightEl = document.getElementById('cart-total-weight');
  const cartTotalPriceEl = document.getElementById('cart-total-price');
  const warningEl = document.getElementById('bulk-warning');
  const checkoutBtn = document.getElementById('checkout-btn');

  const cartKeys = Object.keys(cart);

  if (cartKeys.length === 0) {
    cartContainer.innerHTML = `<p class="empty-cart-msg">Select produce items from the grid to build your wholesale order.</p>`;
    cartTotalWeightEl.textContent = '0 kg';
    cartTotalPriceEl.textContent = '₹0';
    warningEl.classList.add('hidden');
    checkoutBtn.disabled = true;
    return;
  }

  cartContainer.innerHTML = '';
  let totalWeight = 0;
  let totalPrice = 0;
  let hasInvalidLimit = false;

  cartKeys.forEach(key => {
    const item = cart[key];
    const itemTotal = item.quantity * item.product.pricePerKg;
    totalWeight += item.quantity;
    totalPrice += itemTotal;

    if (!item.isValid) {
      hasInvalidLimit = true;
    }

    const itemEl = document.createElement('div');
    itemEl.className = 'cart-item';
    itemEl.innerHTML = `
      <div>
        <strong>${item.product.name}</strong><br/>
        <small>${item.quantity} kg × ₹${item.product.pricePerKg}</small>
        ${!item.isValid ? `<br/><small style="color:var(--terracotta);">Min requirement: ${item.product.minLimitKg} kg</small>` : ''}
      </div>
      <div><strong>₹${itemTotal}</strong></div>
    `;
    cartContainer.appendChild(itemEl);
  });

  cartTotalWeightEl.textContent = `${totalWeight} kg`;
  cartTotalPriceEl.textContent = `₹${totalPrice}`;

  if (hasInvalidLimit) {
    warningEl.classList.remove('hidden');
    checkoutBtn.disabled = true;
  } else {
    warningEl.classList.add('hidden');
    checkoutBtn.disabled = false;
  }
}

// Authentication Modal UI Handlers
function openAuthModal() {
  document.getElementById('auth-modal').classList.remove('hidden');
}

function closeAuthModal() {
  document.getElementById('auth-modal').classList.add('hidden');
}

function switchTab(tab) {
  const signupForm = document.getElementById('signup-form');
  const signinForm = document.getElementById('signin-form');
  const tabSignup = document.getElementById('tab-signup');
  const tabSignin = document.getElementById('tab-signin');

  if (tab === 'signup') {
    signupForm.classList.remove('hidden');
    signinForm.classList.add('hidden');
    tabSignup.classList.add('active');
    tabSignin.classList.remove('active');
  } else {
    signinForm.classList.remove('hidden');
    signupForm.classList.add('hidden');
    tabSignin.classList.add('active');
    tabSignup.classList.remove('active');
  }
}

// Sign Up Handler
function handleSignUp(e) {
  e.preventDefault();
  const phone = document.getElementById('signup-phone').value;
  const password = document.getElementById('signup-password').value;

  const users = JSON.parse(localStorage.getItem('agri_users') || '{}');
  
  if (users[phone]) {
    alert('Phone number is already registered. Please Sign In.');
    switchTab('signin');
    return;
  }

  users[phone] = { password: password };
  localStorage.setItem('agri_users', JSON.stringify(users));
  
  authenticatedUser = phone;
  localStorage.setItem('agri_logged_user', phone);
  updateAuthUI();
  closeAuthModal();
  alert('Account created and signed in successfully!');
}

// Sign In Handler
function handleSignIn(e) {
  e.preventDefault();
  const phone = document.getElementById('signin-phone').value;
  const password = document.getElementById('signin-password').value;

  const users = JSON.parse(localStorage.getItem('agri_users') || '{}');

  if (!users[phone] || users[phone].password !== password) {
    alert('Invalid phone number or password.');
    return;
  }

  authenticatedUser = phone;
  localStorage.setItem('agri_logged_user', phone);
  updateAuthUI();
  closeAuthModal();
  alert('Signed in successfully!');
}

function checkPersistedAuth() {
  const savedUser = localStorage.getItem('agri_logged_user');
  if (savedUser) {
    authenticatedUser = savedUser;
    updateAuthUI();
  }
}

function updateAuthUI() {
  const container = document.getElementById('auth-status-container');
  if (authenticatedUser) {
    container.innerHTML = `
      <span style="color:#d8e5d9; font-weight:600; margin-right:10px;">📱 ${authenticatedUser}</span>
      <button class="btn" style="background:#c85a32; color:#fff;" onclick="handleSignOut()">Sign Out</button>
    `;
  } else {
    container.innerHTML = `<button class="btn btn-primary" onclick="openAuthModal()">Sign In / Sign Up</button>`;
  }
}

function handleSignOut() {
  authenticatedUser = null;
  localStorage.removeItem('agri_logged_user');
  updateAuthUI();
}

// Razorpay Sandbox Checkout Integration
function initiateCheckout() {
  if (!authenticatedUser) {
    alert('Please sign in or create an account before proceeding to checkout.');
    openAuthModal();
    return;
  }

  let totalAmount = 0;
  Object.keys(cart).forEach(key => {
    totalAmount += cart[key].quantity * cart[key].product.pricePerKg;
  });

  if (totalAmount <= 0) return;

  // Razorpay Sandbox Config Options
  const options = {
    key: "rzp_test_TY33dT2JPn537J", // Replace with your test key ID from Razorpay Dashboard
    amount: totalAmount * 100, // Amount in paise
    currency: "INR",
    name: "AgriDirect Bulk Supply",
    description: "Wholesale Farm Produce Order",
    image: "https://images.unsplash.com/photo-1500937386664-56d1dfef3854?auto=format&fit=crop&q=80&w=100",
    handler: function (response) {
      alert(`Payment Successful!\nRazorpay Payment ID: ${response.razorpay_payment_id}\nOrder will be processed by the farm network.`);
      cart = {};
      renderProducts();
      renderCartSummary();
    },
    prefill: {
      contact: authenticatedUser
    },
    theme: {
      color: "#2d5a27"
    }
  };

  const rzp = new Razorpay(options);
  rzp.on('payment.failed', function (response) {
    alert(`Payment Failed: ${response.error.description}`);
  });
  
  rzp.open();
}