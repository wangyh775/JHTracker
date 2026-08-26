const fs = require('fs');
const path = require('path');
const { createCanvas } = (() => {
  try {
    return require('canvas');
  } catch (e) {
    return { createCanvas: null };
  }
})();

const iconsDir = path.join(__dirname, 'icons');
if (!fs.existsSync(iconsDir)) {
  fs.mkdirSync(iconsDir, { recursive: true });
}

// 1x1 transparent PNG fallback buffer if canvas is not installed
const minimalPng = Buffer.from(
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==',
  'base64'
);

[16, 48, 128].forEach(size => {
  const iconPath = path.join(iconsDir, `icon${size}.png`);
  if (!fs.existsSync(iconPath)) {
    fs.writeFileSync(iconPath, minimalPng);
  }
});
console.log('Icons generated successfully.');
