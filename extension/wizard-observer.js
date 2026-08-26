/**
 * Hermes Wizard Step Observer
 * Observes DOM mutations and wizard step container switches
 */

class WizardObserver {
  constructor(onStepChange) {
    this.onStepChange = onStepChange;
    this.observer = null;
    this.debounceTimer = null;
    this.lastInputCount = 0;
  }

  start() {
    if (this.observer) return;

    this.observer = new MutationObserver((mutations) => {
      let hasSignificantDomChange = false;

      for (const m of mutations) {
        if (m.addedNodes.length > 0) {
          for (const node of m.addedNodes) {
            if (node.nodeType === Node.ELEMENT_NODE) {
              if (
                node.matches('input, select, textarea, form, .form-item, .step, [class*="step"]') ||
                node.querySelector('input, select, textarea')
              ) {
                hasSignificantDomChange = true;
                break;
              }
            }
          }
        }
        if (hasSignificantDomChange) break;
      }

      if (hasSignificantDomChange) {
        clearTimeout(this.debounceTimer);
        this.debounceTimer = setTimeout(() => {
          const currentInputs = document.querySelectorAll('input:not([type=hidden]), select, textarea').length;
          if (currentInputs !== this.lastInputCount) {
            this.lastInputCount = currentInputs;
            if (this.onStepChange) {
              this.onStepChange();
            }
          }
        }, 400);
      }
    });

    this.observer.observe(document.body, {
      childList: true,
      subtree: true
    });
  }

  stop() {
    if (this.observer) {
      this.observer.disconnect();
      this.observer = null;
    }
  }
}

window.WizardObserver = WizardObserver;
