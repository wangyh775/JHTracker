/**
 * Hermes Typing Engine
 * Injects synthetic keystrokes with Gaussian jitter, punctuation pauses,
 * and sets prototype values to trigger reactive state changes in React/Vue/Angular.
 */

class TypingEngine {
  constructor() {
    this.isPaused = false;
    this.activeElement = null;
  }

  /**
   * Type text into target element with human-like rhythm
   * @param {HTMLElement} element - input or textarea
   * @param {string} text - text to type
   * @param {Function} onProgress - callback with (charsTyped, totalChars)
   * @param {Function} onComplete - callback when typing completes
   */
  async typeText(element, text, onProgress = null, onComplete = null) {
    if (!element || !text) return;

    this.isPaused = false;
    this.activeElement = element;
    element.focus();

    // Attach pause listener on user intervention
    const userInterruptHandler = () => {
      this.isPaused = true;
    };
    element.addEventListener('mousedown', userInterruptHandler, { once: true });
    element.addEventListener('keydown', userInterruptHandler, { once: true });

    let currentVal = '';
    const totalChars = text.length;

    for (let i = 0; i < totalChars; i++) {
      if (this.isPaused) {
        console.log('[TypingEngine] Paused by user intervention.');
        break;
      }

      const char = text[i];
      currentVal += char;

      // Dispatch beforeinput
      element.dispatchEvent(new InputEvent('beforeinput', {
        data: char,
        inputType: 'insertText',
        bubbles: true,
        cancelable: true
      }));

      // Set property value safely across React / Vue controlled inputs
      this.setNativeValue(element, currentVal);

      // Dispatch input & key events
      element.dispatchEvent(new InputEvent('input', {
        data: char,
        inputType: 'insertText',
        bubbles: true
      }));

      if (onProgress) {
        onProgress(i + 1, totalChars);
      }

      // Delay logic: 35-60 chars/sec => 15-30ms baseline + jitter + punctuation pause
      let delay = 15 + Math.random() * 20;
      if (['。', '！', '？', '.', '!', '?'].includes(char)) {
        delay += 120 + Math.random() * 80;
      } else if (['，', '、', ',', ';', '；'].includes(char)) {
        delay += 60 + Math.random() * 40;
      } else if (char === '\n') {
        delay += 200 + Math.random() * 100;
      }

      await new Promise(r => setTimeout(r, delay));
    }

    // Final change & blur events
    element.dispatchEvent(new Event('change', { bubbles: true }));
    element.dispatchEvent(new Event('blur', { bubbles: true }));
    element.dataset.hermesFilled = 'true';

    element.removeEventListener('mousedown', userInterruptHandler);
    element.removeEventListener('keydown', userInterruptHandler);

    if (onComplete) onComplete(!this.isPaused);
  }

  /**
   * Set native value bypassing React/Vue prototype setter overrides
   */
  setNativeValue(element, value) {
    const proto = Object.getPrototypeOf(element);
    const valueSetter = Object.getOwnPropertyDescriptor(proto, 'value')?.set
      || Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set
      || Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value')?.set;

    if (valueSetter) {
      valueSetter.call(element, value);
    } else {
      element.value = value;
    }
  }

  /**
   * Instant set without typing animation
   */
  instantSet(element, value) {
    this.setNativeValue(element, value);
    element.dispatchEvent(new InputEvent('input', { bubbles: true }));
    element.dispatchEvent(new Event('change', { bubbles: true }));
    element.dataset.hermesFilled = 'true';
  }

  pause() {
    this.isPaused = true;
  }
}

window.TypingEngine = TypingEngine;
