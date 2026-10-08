// Optional DOM integration checks. Requires jsdom on NODE_PATH.
// Usage: node tools/check_interactions.cjs /path/to/hugo/output
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { JSDOM } = require('jsdom');

const output = path.resolve(process.argv[2] || 'public');
const script = fs.readFileSync(path.join(__dirname, '../assets/js/catalog.js'), 'utf8');
const setup = (route, query = '') => {
  const dom = new JSDOM(fs.readFileSync(path.join(output, route, 'index.html'), 'utf8'), {
    // Scripting enabled makes <noscript> inert, as it is in the real browser.
    // External resource loading stays disabled; the local script is evaluated below.
    url: `http://localhost:1313/${route}/${query}`, runScripts: 'dangerously',
  });
  dom.window.matchMedia = () => ({ addEventListener() {} });
  dom.window.HTMLElement.prototype.scrollIntoView = function () {};
  dom.window.eval(script);
  return dom;
};
const input = (dom, selector, value, event = 'input') => {
  const element = dom.window.document.querySelector(selector);
  element.value = value;
  element.dispatchEvent(new dom.window.Event(event, { bubbles: true }));
};
const visible = (dom) => [...dom.window.document.querySelectorAll('[data-product]')].filter((card) => !card.hidden);

(async () => {
  const catalogue = setup('products');
  const document = catalogue.window.document;
  assert.equal(visible(catalogue).length, 52);
  assert.equal(document.querySelector('[data-catalog-controls]').hidden, false);
  input(catalogue, '#product-search', '  sphd60-11  ');
  assert.deepEqual(visible(catalogue).map((card) => card.id), ['p03-01-sphd60-11']);
  assert.equal(new URL(catalogue.window.location.href).searchParams.get('q'), 'sphd60-11');
  input(catalogue, '#product-search', 'STHD80-40');
  assert.equal(visible(catalogue).length, 3, 'Shared component must remain in all applicable series');
  input(catalogue, '#series-filter', '88-sliding', 'change');
  assert.deepEqual(visible(catalogue).map((card) => card.id), ['p07-06-sthd80-40']);
  input(catalogue, '#product-search', 'not-a-product');
  assert.equal(visible(catalogue).length, 0);
  assert.equal(document.querySelector('[data-empty-state]').hidden, false);
  document.querySelector('[data-clear-search]').click();
  assert.equal(visible(catalogue).length, 52);
  assert.equal(catalogue.window.location.search, '');
  input(catalogue, '#product-search', 'casement frame');
  assert.equal(visible(catalogue).length, 7, 'Search includes casement frames and their frame glass beads');
  const restored = setup('products', '?q=STHD80-40&series=80-sliding');
  assert.deepEqual(visible(restored).map((card) => card.id), ['p05-06-sthd80-40']);
  const series = setup('products/60-casement');
  assert.equal(visible(series).length, 15);
  input(series, '#product-search', 'SPHD60-21');
  assert.equal(visible(series).length, 2, 'Repeated printed entries must retain separate references');

  const toggle = document.querySelector('.menu-toggle');
  toggle.click();
  assert.equal(toggle.getAttribute('aria-expanded'), 'true');
  assert.equal(document.querySelector('#site-navigation').classList.contains('is-open'), true);
  document.dispatchEvent(new catalogue.window.KeyboardEvent('keydown', { key: 'Escape' }));
  assert.equal(toggle.getAttribute('aria-expanded'), 'false');
  assert.equal(document.activeElement, toggle);

  const enquiryLink = document.querySelector('#p03-01-sphd60-11 .product-actions .btn').href;
  const contact = setup('contact', new URL(enquiryLink).search);
  const contactDocument = contact.window.document;
  const form = contactDocument.querySelector('#enquiry-form');
  assert.equal(form.elements.product.value, 'SPHD60-11 · 60 Casement Series');
  assert.equal(form.elements.reference.value, 'Page 3, entry 1');
  assert.equal(contactDocument.querySelector('#prepare-enquiry').disabled, false);
  form.dispatchEvent(new contact.window.Event('submit', { cancelable: true }));
  assert.equal(contactDocument.querySelector('#email-draft').hidden, true, 'Invalid form must not create a draft');
  form.elements.name.value = 'A & B Fabricators';
  form.elements.email.value = 'fabricator@example.test';
  form.elements.company.value = 'Window Works';
  form.elements.quantity.value = '12 bags';
  form.elements.message.value = 'Please quote 12 bags.\nRequired in Coimbatore. <drawing attached separately>';
  form.dispatchEvent(new contact.window.Event('submit', { cancelable: true }));
  assert.equal(contactDocument.querySelector('#email-draft').hidden, false);
  assert.match(contactDocument.querySelector('#draft-status').textContent, /not been sent/);
  const mailto = new URL(contactDocument.querySelector('#open-email-app').href);
  assert.equal(mailto.protocol, 'mailto:');
  assert.equal(mailto.pathname, 'kalpanaupvctraders@gmail.com');
  assert.match(mailto.searchParams.get('subject'), /SPHD60-11/);
  assert.match(mailto.searchParams.get('body'), /Catalogue reference: Page 3, entry 1/);
  assert.match(mailto.searchParams.get('body'), /Name: A & B Fabricators/);
  assert.match(mailto.searchParams.get('body'), /Quantity: 12 bags/);
  assert.match(mailto.searchParams.get('body'), /<drawing attached separately>/);
  let copied;
  contact.window.navigator.clipboard = { async writeText(value) { copied = value; } };
  contactDocument.querySelector('#copy-enquiry').click();
  await new Promise((resolve) => setImmediate(resolve));
  assert.equal(copied, contactDocument.querySelector('#draft-text').value);
  delete contact.window.navigator.clipboard;
  contactDocument.querySelector('#copy-enquiry').click();
  assert.match(contactDocument.querySelector('#draft-status').textContent, /Select and copy/);
  assert.equal(contactDocument.querySelector('#draft-text').selectionEnd, copied.length);

  for (const dom of [catalogue, restored, series, contact]) dom.window.close();
  console.log('PASS: search, series filters, shared/duplicate codes, URL filters, mobile menu state, enquiry prefill, validation, email encoding, and copy fallback.');
})().catch((error) => { console.error(error); process.exitCode = 1; });
