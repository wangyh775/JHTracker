/**
 * Hermes Form Detector
 * Heuristic extractor for DOM fields on modern ATS portals
 */

class FormDetector {
  /**
   * Scan page and return array of detected inputs with metadata
   */
  static scan() {
    const inputs = [];
    const elements = document.querySelectorAll(
      'input:not([type="hidden"]):not([type="submit"]):not([type="button"]), select, textarea'
    );

    elements.forEach((el, index) => {
      // Skip if inside our widget or not visible
      if (el.closest('career-tracker-widget') || !this.isVisible(el)) return;

      const label = this.resolveLabel(el);
      const type = el.tagName.toLowerCase() === 'textarea'
        ? 'textarea'
        : el.tagName.toLowerCase() === 'select'
          ? 'select'
          : el.type || 'text';

      const fieldInfo = {
        id: el.id || `hermes_field_${index}`,
        element: el,
        tagName: el.tagName.toLowerCase(),
        type: type,
        name: el.name || '',
        placeholder: el.placeholder || '',
        label: label,
        required: el.required || el.getAttribute('aria-required') === 'true' || label.includes('*'),
        value: el.value || '',
        filled: el.dataset.hermesFilled === 'true'
      };

      // Extract options if select or radio/checkbox
      if (type === 'select') {
        fieldInfo.options = Array.from(el.options).map(o => ({ value: o.value, text: o.text.trim() }));
      }

      inputs.push(fieldInfo);
    });

    return inputs;
  }

  /**
   * Resolve semantic label for input element
   */
  static resolveLabel(el) {
    // 1. Explicit <label for="id">
    if (el.id) {
      const labelEl = document.querySelector(`label[for="${el.id}"]`);
      if (labelEl && labelEl.innerText.trim()) {
        return labelEl.innerText.trim();
      }
    }

    // 2. Closest wrapping label
    const parentLabel = el.closest('label');
    if (parentLabel && parentLabel.innerText.trim()) {
      return parentLabel.innerText.trim();
    }

    // 3. aria-label or placeholder or name
    if (el.getAttribute('aria-label')) return el.getAttribute('aria-label').trim();
    if (el.placeholder) return el.placeholder.trim();

    // 4. Look at previous sibling or closest form-item label
    const formItem = el.closest('.form-item, .ant-form-item, .el-form-item, .form-group, .item, .row');
    if (formItem) {
      const itemLabel = formItem.querySelector('label, .label, .title, .ant-form-item-label, .el-form-item__label');
      if (itemLabel && itemLabel.innerText.trim()) {
        return itemLabel.innerText.trim();
      }
    }

    return el.name || el.id || '未命名字段';
  }

  static isVisible(el) {
    return !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
  }
}

window.FormDetector = FormDetector;
