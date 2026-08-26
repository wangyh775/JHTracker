/**
 * Hermes Content Script Entrypoint
 * Mounts Shadow DOM widget, extracts ticket/hash, fetches payload, and starts wizard observer.
 */

(function () {
  // Prevent duplicate execution inside the same window/frame
  if (window.__hermes_content_script_injected__) return;
  window.__hermes_content_script_injected__ = true;

  console.log('[Hermes Content Script] Initialized on:', window.location.href);

  // 1. Extract Ticket or App ID from Hash or Query Params
  let appId = null;
  const hash = window.location.hash;
  if (hash.includes('hermes_app_id=')) {
    const match = hash.match(/hermes_app_id=([0-9]+)/);
    if (match) {
      appId = parseInt(match[1], 10);
      try {
        history.replaceState(null, document.title, window.location.pathname + window.location.search);
      } catch (e) {}
    }
  }
  if (!appId) {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('hermes_app_id')) {
      appId = parseInt(urlParams.get('hermes_app_id'), 10);
    }
  }

  // 2. Mount Career Tracker Shadow DOM Widget
  function mountWidget() {
    if (!document.body) {
      document.addEventListener('DOMContentLoaded', mountWidget);
      return;
    }
    let widget = document.querySelector('career-tracker-widget');
    if (!widget) {
      widget = document.createElement('career-tracker-widget');
      document.body.appendChild(widget);
      console.log('[Hermes Content Script] Widget mounted successfully.');
    }
    return widget;
  }

  const widget = mountWidget();

  // 3. Fetch Autofill Payload from Background Service Worker
  function loadPayload() {
    try {
      chrome.runtime.sendMessage({
        type: 'GET_AUTOFILL_PAYLOAD',
        payload: {
          appId: appId,
          url: window.location.href
        }
      }, (response) => {
        if (chrome.runtime.lastError) {
          console.warn('[Hermes Content Script] Message error:', chrome.runtime.lastError.message);
          return;
        }
        if (response && response.success && response.data) {
          console.log('[Hermes Content Script] Payload loaded:', response.data);
          const w = document.querySelector('career-tracker-widget') || widget;
          if (w && typeof w.setPayload === 'function') {
            w.setPayload(response.data);
          }
        } else {
          console.log('[Hermes Content Script] No matching active application payload found for current URL.');
        }
      });
    } catch (err) {
      console.error('[Hermes Content Script] Failed to send message to background:', err);
    }
  }

  loadPayload();

  // 4. Initial Form Scan & Wizard Step Observer
  function scanAndReport() {
    if (typeof FormDetector !== 'undefined') {
      const detected = FormDetector.scan();
      const w = document.querySelector('career-tracker-widget') || widget;
      if (w && typeof w.updateDetectedFields === 'function') {
        w.updateDetectedFields(detected);
      }
    }
  }

  setTimeout(scanAndReport, 800);

  if (typeof WizardObserver !== 'undefined') {
    const wizardObserver = new WizardObserver(() => {
      console.log('[Hermes Content Script] Step / DOM change detected, re-scanning...');
      scanAndReport();
    });
    wizardObserver.start();
  }

  // 5. Intercept Submit Event for status synchronization
  document.addEventListener('submit', (e) => {
    if (appId) {
      console.log('[Hermes Content Script] Form submit detected, syncing status...');
      chrome.runtime.sendMessage({
        type: 'SYNC_SUBMITTED',
        payload: {
          appId: appId,
          status: '已投递',
          notes: '由 Hermes 浏览器插件网申助手辅助提交'
        }
      });
    }
  }, true);
})();
