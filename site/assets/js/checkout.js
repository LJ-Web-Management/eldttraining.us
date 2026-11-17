// eldttraining.us checkout — Stripe card element + hazwoper-osha.com course API
// Flow mirrors datacentertraining.us: Stripe createPaymentMethod -> /add_new_user -> /add_order -> confirmCardPayment
document.addEventListener('DOMContentLoaded', function () {

  var stripeCheckoutForm = document.getElementById('stripeCheckoutForm');
  if (!stripeCheckoutForm) return;

  var apiBaseUrl = window.API_BASE_URL || (typeof API_BASE_URL !== 'undefined' ? API_BASE_URL : 'https://hazwoper-osha.com/api');
  var activeStripeKey = (typeof STRIPE_PUBLISHABLE_KEY !== 'undefined' && STRIPE_PUBLISHABLE_KEY)
    ? STRIPE_PUBLISHABLE_KEY
    : (window.STRIPE_PUBLISHABLE_KEY || '');
  var checkoutDisabled = (typeof CHECKOUT_DISABLED !== 'undefined' && CHECKOUT_DISABLED);

  var stripe = null;
  var elements = null;
  var cardElement = null;
  var currentOrderDetails = null;

  var submitPaymentBtn = document.getElementById('submitPaymentBtn');
  var paymentErrorAlert = document.getElementById('payment-error');
  var checkoutSuccessView = document.getElementById('checkoutSuccessView');
  var courseSelect = document.getElementById('courseSelect');

  var track = function () { if (typeof window.gtag === 'function') { try { window.gtag.apply(null, arguments); } catch (e) {} } };

  var getErrorMessage = function (err) {
    if (!err) return 'Payment failed. Please check your card details and try again.';
    if (typeof err === 'string') return err;
    if (err.message && typeof err.message === 'string') return err.message;
    if (err.error && typeof err.error === 'string') return err.error;
    if (err.error && err.error.message && typeof err.error.message === 'string') return err.error.message;
    try { return JSON.stringify(err); } catch (e) { return 'An unexpected error occurred during payment processing.'; }
  };

  // ?item=<slug|handle|id> (also accepts ?course=)
  var urlParams = new URLSearchParams(window.location.search);
  var itemKey = urlParams.get('item') || urlParams.get('course') || 'class-a';
  var selected = (typeof findEldtItem === 'function') ? findEldtItem(itemKey) : null;
  if (!selected) selected = findEldtItem('class-a');

  var fmt = function (amt) {
    if (typeof formatMoney === 'function') return formatMoney(amt);
    return Number(amt).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  };

  var getStripe = function () {
    if (stripe) return stripe;
    if (window.Stripe && activeStripeKey) {
      stripe = window.Stripe(activeStripeKey);
    } else {
      console.error('Stripe.js SDK not loaded');
    }
    return stripe;
  };

  var setButtonLoading = function (isLoading) {
    if (!submitPaymentBtn) return;
    var btnText = submitPaymentBtn.querySelector('.btn-text');
    var btnSpinner = submitPaymentBtn.querySelector('.btn-spinner');
    submitPaymentBtn.disabled = isLoading || checkoutDisabled;
    if (btnText) btnText.hidden = isLoading;
    if (btnSpinner) btnSpinner.hidden = !isLoading;
  };

  var renderSummary = function () {
    currentOrderDetails = {
      itemSlug: selected.slug,
      name: selected.name,
      type: selected.type,
      courseIds: [selected.courseId],
      basePrice: selected.price,
      totalPrice: selected.price
    };
    var set = function (id, v) { var el = document.getElementById(id); if (el) el.textContent = v; };
    set('summaryCourseName', selected.name);
    set('summaryCourseQty', 'Qty: 1 · Online theory course');
    set('summaryCourseAmount', '$' + fmt(selected.price));
    set('summarySubtotal', '$' + fmt(selected.price));
    set('summaryTotal', '$' + fmt(selected.price));
    var wasEl = document.getElementById('summaryCompareAt');
    if (wasEl) {
      if (selected.compareAt && selected.compareAt > selected.price) {
        wasEl.hidden = false;
        wasEl.textContent = 'Regular $' + fmt(selected.compareAt) + ' · You save $' + fmt(selected.compareAt - selected.price);
      } else { wasEl.hidden = true; }
    }
    var back = document.getElementById('summaryCourseLink');
    if (back) back.href = '/products/' + selected.handle;
    if (courseSelect) courseSelect.value = selected.slug;
  };

  var beginCheckoutEvent = function () {
    track('event', 'begin_checkout', { currency: 'USD', value: selected.price, items: [gaItem(selected)] });
  };

  var initCheckoutPage = function () {
    renderSummary();
    beginCheckoutEvent();

    if (courseSelect) {
      courseSelect.addEventListener('change', function () {
        var next = findEldtItem(courseSelect.value);
        if (!next) return;
        selected = next;
        renderSummary();
        beginCheckoutEvent();
        try {
          var u = new URL(window.location.href); u.searchParams.set('item', selected.slug);
          window.history.replaceState({}, '', u.toString());
        } catch (e) {}
      });
    }

    var stripeInstance = getStripe();
    if (!stripeInstance) return;
    var container = document.getElementById('payment-element');
    if (!container) return;

    try {
      elements = stripeInstance.elements();
      cardElement = elements.create('card', {
        style: {
          base: {
            fontSize: '16px',
            color: '#222222',
            fontFamily: "'Open Sans', -apple-system, BlinkMacSystemFont, sans-serif",
            '::placeholder': { color: '#9aa0a3' }
          },
          invalid: { color: '#c62828' }
        }
      });
      container.innerHTML = '';
      cardElement.mount('#payment-element');
    } catch (err) {
      console.warn('Error mounting Stripe Card Element:', err);
    }

    if (checkoutDisabled && submitPaymentBtn) {
      submitPaymentBtn.disabled = true;
      submitPaymentBtn.setAttribute('aria-disabled', 'true');
      var btnText = submitPaymentBtn.querySelector('.btn-text');
      if (btnText) btnText.textContent = 'Enrollment Opening Soon';
    }
  };

  // International phone input
  var iti = null;
  var phoneInput = document.getElementById('billingPhone');
  var phoneErrorEl = document.getElementById('phone-error');

  if (phoneInput && window.intlTelInput) {
    iti = window.intlTelInput(phoneInput, {
      initialCountry: 'us',
      preferredCountries: ['us', 'ca'],
      separateDialCode: true,
      autoPlaceholder: 'polite',
      formatOnDisplay: true,
      utilsScript: 'https://cdn.jsdelivr.net/npm/intl-tel-input@18.2.1/build/js/utils.js'
    });

    phoneInput.addEventListener('input', function () {
      if (phoneErrorEl) phoneErrorEl.hidden = true;
      if (iti && window.intlTelInputUtils) {
        var currentVal = phoneInput.value;
        var formatted = iti.getNumber(window.intlTelInputUtils.numberFormat.NATIONAL);
        if (formatted && currentVal.length >= 3) phoneInput.value = formatted;
      }
    });

    phoneInput.addEventListener('blur', function () {
      if (phoneInput.value.trim() !== '') {
        if (!iti.isValidNumber()) {
          if (phoneErrorEl) { phoneErrorEl.textContent = 'Please enter a valid phone number.'; phoneErrorEl.hidden = false; }
        } else if (phoneErrorEl) {
          phoneErrorEl.hidden = true;
        }
      }
    });
  }

  var val = function (id) { var el = document.getElementById(id); return el ? el.value.trim() : ''; };

  stripeCheckoutForm.addEventListener('submit', async function (e) {
    e.preventDefault();

    if (checkoutDisabled) {
      if (paymentErrorAlert) {
        paymentErrorAlert.textContent = 'Online enrollment is temporarily unavailable. Call (866) 429-6742 or email info@eldttraining.us to enroll.';
        paymentErrorAlert.hidden = false;
      }
      return;
    }

    setButtonLoading(true);
    if (paymentErrorAlert) { paymentErrorAlert.hidden = true; paymentErrorAlert.textContent = ''; }
    if (phoneErrorEl) phoneErrorEl.hidden = true;

    if (iti && phoneInput && phoneInput.value.trim() !== '' && !iti.isValidNumber()) {
      if (phoneErrorEl) { phoneErrorEl.textContent = 'Please enter a valid phone number before proceeding.'; phoneErrorEl.hidden = false; }
      phoneInput.focus();
      setButtonLoading(false);
      return;
    }

    var firstName = val('billingFirstName');
    var lastName = val('billingLastName');
    var company = val('billingCompany');
    var phone = (iti && typeof iti.getNumber === 'function') ? iti.getNumber() : val('billingPhone');
    var userEmail = val('billingEmail');
    var address1 = val('billingAddress');
    var address2 = val('billingAddress2');
    var city = val('billingCity');
    var state = val('billingState');
    var zip = val('billingZip');
    var country = document.getElementById('billingCountry') ? document.getElementById('billingCountry').value : 'US';

    track('event', 'add_payment_info', { currency: 'USD', value: selected.price, payment_type: 'card', items: [gaItem(selected)] });

    var stripeInstance = getStripe();
    if (!stripeInstance || !cardElement) {
      if (paymentErrorAlert) { paymentErrorAlert.textContent = 'Stripe payment SDK is not initialized. Please refresh the page.'; paymentErrorAlert.hidden = false; }
      setButtonLoading(false);
      return;
    }

    // STEP 1: Create the Stripe PaymentMethod
    var pmResult = await stripeInstance.createPaymentMethod({
      type: 'card',
      card: cardElement,
      billing_details: {
        name: firstName + ' ' + lastName,
        email: userEmail,
        phone: phone,
        address: { line1: address1, line2: address2, city: city, state: state, postal_code: zip, country: country }
      }
    });

    if (pmResult.error) {
      if (paymentErrorAlert) { paymentErrorAlert.textContent = getErrorMessage(pmResult.error); paymentErrorAlert.hidden = false; }
      setButtonLoading(false);
      return;
    }

    var paymentMethodId = pmResult.paymentMethod ? pmResult.paymentMethod.id : '';

    // STEP 2: Create / look up the LMS user
    var customerId = 0;
    try {
      var addUserRes = await fetch(apiBaseUrl + '/add_new_user', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ first_name: firstName, last_name: lastName, email: userEmail, user_name: firstName + ' ' + lastName, user_role_id: 2, phone: phone })
      });
      if (addUserRes.ok) {
        var userData = await addUserRes.json();
        if (userData) {
          customerId = userData.user_id ||
            (userData.data && userData.data.user_id) ||
            (userData.success && userData.success.user_id) ||
            (userData.user && userData.user.user_id) || 0;
        }
      }
    } catch (userErr) {
      console.warn('add_new_user API call notice:', userErr);
    }

    // STEP 3: Create the order (course enrollment) and confirm the payment
    var orderId = 'ELDT-' + Math.floor(100000 + Math.random() * 900000);
    try {
      var orderPayload = {
        customer_id: customerId,
        payment_method: 'stripe',
        payment_method_id: paymentMethodId,
        order_type: 'normal',
        order_status: 'pending',
        order_from: 'eldttraining.us',
        billing_first_name: firstName,
        billing_last_name: lastName,
        billing_name: firstName + ' ' + lastName,
        billing_email: userEmail,
        billing_phone: phone,
        billing_company: company,
        billing_address_1: address1,
        billing_address_2: address2,
        billing_city: city,
        billing_state: state,
        billing_postcode: zip,
        billing_country: country,
        shipping_address_1: address1,
        shipping_address_2: address2,
        shipping_city: city,
        shipping_state: state,
        shipping_postcode: zip,
        shipping_country: country,
        courses: currentOrderDetails.courseIds.map(function (cid) {
          return { course_id: cid, quantity: 1, users: [{ first_name: firstName, last_name: lastName, email: userEmail, user_name: '' }] };
        })
      };

      var addOrderRes = await fetch(apiBaseUrl + '/add_order', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(orderPayload)
      });

      if (addOrderRes.ok) {
        var orderData = await addOrderRes.json();

        if (orderData && (orderData.success === false || orderData.error)) {
          if (paymentErrorAlert) { paymentErrorAlert.textContent = getErrorMessage(orderData.error || orderData); paymentErrorAlert.hidden = false; }
          setButtonLoading(false);
          return;
        }

        if (orderData && (orderData.order_id || orderData.id)) {
          orderId = '#' + (orderData.order_id || orderData.id);
        }

        if (orderData && orderData.clientSecret && stripeInstance) {
          var confirmRes;
          if (paymentMethodId) {
            confirmRes = await stripeInstance.confirmCardPayment(orderData.clientSecret, { payment_method: paymentMethodId });
          } else {
            confirmRes = await stripeInstance.confirmCardPayment(orderData.clientSecret, {
              payment_method: { card: cardElement, billing_details: { name: firstName + ' ' + lastName, email: userEmail, phone: phone } }
            });
          }
          if (confirmRes && confirmRes.error) {
            if (paymentErrorAlert) { paymentErrorAlert.textContent = getErrorMessage(confirmRes.error); paymentErrorAlert.hidden = false; }
            setButtonLoading(false);
            return;
          }
        }
      } else {
        var errorData = null;
        try { errorData = await addOrderRes.json(); } catch (je) { errorData = 'Order could not be created (HTTP ' + addOrderRes.status + ').'; }
        if (paymentErrorAlert) { paymentErrorAlert.textContent = getErrorMessage(errorData); paymentErrorAlert.hidden = false; }
        setButtonLoading(false);
        return;
      }
    } catch (orderErr) {
      console.warn('Error executing add_order API:', orderErr);
      if (paymentErrorAlert) { paymentErrorAlert.textContent = getErrorMessage(orderErr); paymentErrorAlert.hidden = false; }
      setButtonLoading(false);
      return;
    }

    // Success: analytics (GA4 purchase + Google Ads conversion w/ enhanced conversions), then confirmation view
    var txId = String(orderId).replace(/^#/, '');
    track('set', 'user_data', { email: userEmail, phone_number: phone });
    track('event', 'purchase', { transaction_id: txId, currency: 'USD', value: selected.price, items: [gaItem(selected)] });
    if (typeof GOOGLE_ADS_CONVERSION !== 'undefined' && GOOGLE_ADS_CONVERSION) {
      track('event', 'conversion', { send_to: GOOGLE_ADS_CONVERSION, value: selected.price, currency: 'USD', transaction_id: txId });
    }

    stripeCheckoutForm.hidden = true;
    stripeCheckoutForm.style.display = 'none';
    var pageHeader = document.querySelector('.checkout-header');
    if (pageHeader) { pageHeader.hidden = true; pageHeader.style.display = 'none'; }

    if (checkoutSuccessView) {
      document.getElementById('successOrderId').textContent = orderId.charAt(0) === '#' ? orderId : '#' + orderId;
      document.getElementById('successUserEmail').textContent = userEmail || 'your email';
      var sc = document.getElementById('successCourseName'); if (sc) sc.textContent = selected.name;
      checkoutSuccessView.hidden = false;
      checkoutSuccessView.style.display = 'block';
      checkoutSuccessView.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    setButtonLoading(false);
  });

  initCheckoutPage();
});
