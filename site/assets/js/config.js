// PRODUCTION
const STRIPE_PUBLISHABLE_KEY = "pk_live_doCHB0jglD5eISjEmB1vB6mb00xIg51noK";
// const STRIPE_PUBLISHABLE_KEY = "pk_test_51KRElxBHssw16TqHLVweh7MZorffCzySrRWdwAeURnEjnjuNZ7tsIfnmcBq1px0qSGWfJ3Kl2bDQRjaCCJpEO27W005Qidmdci"; // STAGING
const API_BASE_URL = "https://hazwoper-osha.com/api";

// Courses are live in the hazwoper-osha.com LMS catalog, so checkout is enabled.
// Set to true to show "Enrollment Opening Soon" and block payment.
const CHECKOUT_DISABLED = false;

// Google Ads purchase conversion (carried over from the Shopify "Google Ads Purchase Tag" custom pixel).
const GOOGLE_ADS_CONVERSION = "AW-16866056315/qwkRCKWJrp0aEPuwruo-";

// Source of truth for the ELDT catalog.
// id + sku match the hazwoper-osha.com catalog entries (data-id / data-sku on
// hazwoper-osha.com/online-courses/cdl-entry-level-driver-training-eldt-class-a and related cards).
// price / compareAt are the eldttraining.us display prices. NOTE: the amount actually charged is
// set server-side by hazwoper-osha.com's /add_order response, not by these values.
var ELDT_COURSES = [
  { slug: "class-a",         id: 304, sku: "ELDTClassA",       handle: "entry-level-driver-training-eldt-class-a",                         name: "Entry Level Driver Training (ELDT) - Class A",                                   short: "Class A CDL",                  price: 129.99, compareAt: 159.99 },
  { slug: "class-b",         id: 309, sku: "CDL ELDT C-B",     handle: "entry-level-driver-training-eldt-class-b",                         name: "Entry Level Driver Training (ELDT) - Class B",                                   short: "Class B CDL",                  price: 119.99, compareAt: 159.99 },
  { slug: "b-to-a-upgrade",  id: 316, sku: "ELDTB-AUpgrade",   handle: "entry-level-driver-training-eldt-class-b-to-a-upgrade",            name: "Entry Level Driver Training (ELDT) - Class B to A Upgrade",                      short: "Class B to A Upgrade",         price: 99.99,  compareAt: 129.99 },
  { slug: "hazmat-h",        id: 281, sku: "ELDTHEndorsement", handle: "cdl-entry-level-driver-training-eldt-hazmat-h-endorsement",        name: "CDL Entry Level Driver Training (ELDT) - HAZMAT (H) Endorsement",                short: "Hazmat (H) Endorsement",       price: 69.99,  compareAt: 99.99 },
  { slug: "passenger-p",     id: 293, sku: "ELDTPEndorsement", handle: "cdl-entry-level-driver-training-eldt-passenger-p-endorsement",     name: "CDL Entry Level Driver Training (ELDT) - Passenger (P) Endorsement",             short: "Passenger (P) Endorsement",    price: 59.99,  compareAt: 99.99 },
  { slug: "school-bus-s",    id: 299, sku: "CELDTSBS",         handle: "cdl-entry-level-driver-training-eldt-school-bus-s-endorsement",    name: "CDL Entry Level Driver Training (ELDT) - School Bus (S) Endorsement",            short: "School Bus (S) Endorsement",   price: 59.99,  compareAt: 99.00 },
  { slug: "hazmat-tanker-x", id: 493, sku: "X Endorsment",     handle: "entry-level-driver-training-eldt-hazmat-and-tank-vehicle-endorsement", name: "CDL Entry Level Driver Training (ELDT) - Hazmat and Tank Vehicle (X) Endorsement", short: "Hazmat + Tanker (X) Endorsement", price: 129.99, compareAt: 169.00 },
  { slug: "tanker-n",        id: 499, sku: "CDL-ELDT-N",       handle: "cdl-entry-level-driver-training-eldt-tanker-n-endorsement",        name: "CDL Entry Level Driver Training (ELDT) - Tanker (N) Endorsement",                short: "Tanker (N) Endorsement",       price: 49.99,  compareAt: 99.99 }
];

var formatMoney = function (n) {
  return Number(n).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
};

// Look up a course by checkout slug, Shopify-era product handle, or numeric course id.
var findEldtItem = function (key) {
  if (!key) return null;
  key = String(key).toLowerCase();
  var c = ELDT_COURSES.find(function (x) { return x.slug === key || x.handle === key || String(x.id) === key; });
  if (!c) return null;
  return { type: 'course', slug: c.slug, name: c.name, short: c.short, price: c.price, compareAt: c.compareAt, courseId: c.id, sku: c.sku, handle: c.handle };
};

// GA4 ecommerce item shape for a course
var gaItem = function (c) {
  return { item_id: c.sku || String(c.courseId || c.id), item_name: c.name, item_brand: 'ELDT Training', item_category: 'ELDT Theory Course', price: c.price, quantity: 1 };
};

// Mobile nav toggle (shared by all pages; lets checkout run without main.js)
document.addEventListener('DOMContentLoaded', function () {
  var navToggle = document.getElementById('navToggle');
  var mainNav = document.getElementById('mainNav');
  if (navToggle && mainNav && !navToggle.dataset.navWired) {
    navToggle.dataset.navWired = '1';
    navToggle.addEventListener('click', function () {
      var isOpen = mainNav.classList.toggle('open');
      navToggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    });
  }
});
