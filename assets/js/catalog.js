(() => {
  'use strict';

  const menuButton = document.querySelector('.menu-toggle');
  const navigation = document.querySelector('#site-navigation');
  if (menuButton && navigation) {
    const setMenu = (open) => {
      navigation.classList.toggle('is-open', open);
      menuButton.setAttribute('aria-expanded', String(open));
      menuButton.setAttribute('aria-label', open ? 'Close navigation' : 'Open navigation');
    };
    menuButton.addEventListener('click', () => setMenu(menuButton.getAttribute('aria-expanded') !== 'true'));
    navigation.addEventListener('click', (event) => {
      if (event.target.closest('a')) setMenu(false);
    });
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && menuButton.getAttribute('aria-expanded') === 'true') {
        setMenu(false);
        menuButton.focus();
      }
    });
    window.matchMedia('(min-width: 992px)').addEventListener('change', () => setMenu(false));
  }

  const catalogue = document.querySelector('[data-catalog]');
  if (catalogue) {
    const search = catalogue.querySelector('#product-search');
    const series = catalogue.querySelector('#series-filter');
    const cards = [...catalogue.querySelectorAll('[data-product]')];
    const count = catalogue.querySelector('[data-product-count]');
    const empty = catalogue.querySelector('[data-empty-state]');
    const query = new URLSearchParams(window.location.search);
    search.value = (query.get('q') || '').slice(0, 200);
    if (series && [...series.options].some((option) => option.value === query.get('series'))) {
      series.value = query.get('series');
    }
    catalogue.querySelector('[data-catalog-controls]').hidden = false;

    const filter = (updateURL = true) => {
      const terms = search.value.trim().toLowerCase().split(/\s+/).filter(Boolean);
      const selectedSeries = series ? series.value : '';
      let visible = 0;
      cards.forEach((card) => {
        const match = (!selectedSeries || card.dataset.series === selectedSeries)
          && terms.every((term) => card.dataset.search.includes(term));
        card.hidden = !match;
        if (match) visible += 1;
      });
      count.textContent = `${visible} of ${cards.length} catalogue profiles`;
      empty.hidden = visible !== 0;
      if (updateURL) {
        const url = new URL(window.location.href);
        url.searchParams.delete('q');
        url.searchParams.delete('series');
        if (search.value.trim()) url.searchParams.set('q', search.value.trim());
        if (selectedSeries) url.searchParams.set('series', selectedSeries);
        window.history.replaceState(null, '', url);
      }
    };
    search.addEventListener('input', () => filter());
    if (series) series.addEventListener('change', () => filter());
    catalogue.querySelectorAll('[data-clear-search]').forEach((button) => {
      button.addEventListener('click', () => {
        search.value = '';
        if (series) series.value = '';
        filter();
        search.focus();
      });
    });
    filter(false);
  }

  const form = document.querySelector('#enquiry-form');
  if (form) {
    const query = new URLSearchParams(window.location.search);
    const product = query.get('product') || '';
    const series = query.get('series') || '';
    form.elements.product.value = [product, series].filter(Boolean).join(' · ').slice(0, 200);
    form.elements.reference.value = (query.get('reference') || '').slice(0, 200);
    form.querySelector('#prepare-enquiry').disabled = false;
    const draft = form.querySelector('#email-draft');
    const draftText = form.querySelector('#draft-text');
    const status = form.querySelector('#draft-status');

    form.addEventListener('submit', (event) => {
      event.preventDefault();
      if (!form.reportValidity()) return;
      const values = new FormData(form);
      const get = (key) => String(values.get(key) || '').trim();
      const subject = `SRI STAR profile enquiry${get('product') ? ` — ${get('product')}` : ''}`;
      const body = [
        'Hello Kalpana Traders,', '',
        'I would like to enquire about SRI STAR Profiles.', '',
        `Name: ${get('name')}`,
        `Email: ${get('email')}`,
        `Phone: ${get('phone') || 'Not provided'}`,
        `Company: ${get('company') || 'Not provided'}`, '',
        `Product / series: ${get('product') || 'Please help me select a profile'}`,
        `Catalogue reference: ${get('reference') || 'Not specified'}`,
        `Quantity: ${get('quantity') || 'To be discussed'}`, '',
        'Requirements:', get('message'), '', 'Thank you.',
      ].join('\n');
      draftText.value = `Subject: ${subject}\n\n${body}`;
      form.querySelector('#open-email-app').href = `mailto:${form.dataset.email}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
      draft.hidden = false;
      status.textContent = 'Your email draft is ready. It has not been sent.';
      draft.scrollIntoView({ behavior: 'auto', block: 'nearest' });
    });

    form.querySelector('#copy-enquiry').addEventListener('click', async () => {
      try {
        if (!navigator.clipboard) throw new Error('Clipboard unavailable');
        await navigator.clipboard.writeText(draftText.value);
        status.textContent = 'Enquiry copied. Paste it into your email app and send it to Kalpana Traders.';
      } catch {
        draftText.focus();
        draftText.select();
        status.textContent = 'Select and copy the enquiry text, then paste it into your email app.';
      }
    });
  }
})();
