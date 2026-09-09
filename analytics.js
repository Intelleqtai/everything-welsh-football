(() => {
  'use strict';
  const id = 'G-4B8KVJD8MZ';
  const key = 'ewf-analytics-consent-v1';
  const maxAge = 180 * 24 * 60 * 60 * 1000;
  const panel = document.getElementById('analytics-consent');
  let loaded = false;
  let choice = null;
  try {
    const saved = JSON.parse(localStorage.getItem(key));
    if (saved && Date.now() - saved.time < maxAge && ['granted', 'denied'].includes(saved.value)) choice = saved.value;
  } catch (_) {}
  function loadAnalytics() {
    if (loaded || !['everythingwelshfootball.club', 'www.everythingwelshfootball.club'].includes(location.hostname)) return;
    loaded = true;
    window.dataLayer = window.dataLayer || [];
    window.gtag = function () { window.dataLayer.push(arguments); };
    window.gtag('consent', 'default', {
      analytics_storage: 'granted', ad_storage: 'denied',
      ad_user_data: 'denied', ad_personalization: 'denied'
    });
    window.gtag('js', new Date());
    window.gtag('config', id, {
      allow_google_signals: false, allow_ad_personalization_signals: false,
      cookie_expires: 15552000,
      page_location: location.origin + location.pathname,
      page_referrer: document.referrer ? new URL(document.referrer).origin : ''
    });
    const script = document.createElement('script');
    script.async = true;
    script.src = 'https://www.googletagmanager.com/gtag/js?id=' + id;
    document.head.appendChild(script);
  }
  function removeCookies() {
    for (const cookie of document.cookie.split(';')) {
      const name = cookie.trim().split('=')[0];
      if (!/^_ga(?:_|$)/.test(name)) continue;
      for (const domain of ['', location.hostname, '.' + location.hostname, '.everythingwelshfootball.club']) {
        document.cookie = name + '=; Max-Age=0; Path=/; SameSite=Lax' + (domain ? '; Domain=' + domain : '');
      }
    }
  }
  function save(value) {
    try { localStorage.setItem(key, JSON.stringify({value, time: Date.now()})); } catch (_) {}
    panel.hidden = true;
    if (value === 'granted') loadAnalytics();
    else {
      window['ga-disable-' + id] = true;
      removeCookies();
      if (loaded) location.reload();
    }
    document.getElementById('analytics-settings').focus({preventScroll: true});
  }
  document.getElementById('analytics-accept').addEventListener('click', () => { window['ga-disable-' + id] = false; save('granted'); });
  document.getElementById('analytics-decline').addEventListener('click', () => save('denied'));
  document.getElementById('analytics-settings').addEventListener('click', () => {panel.hidden = false; document.getElementById('analytics-decline').focus();});
  if (choice === 'granted') loadAnalytics();
  else { removeCookies(); panel.hidden = choice === 'denied'; }
})();
