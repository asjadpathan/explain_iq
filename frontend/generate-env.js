const fs = require('fs');
const path = require('path');

const backendUrl = process.env.BACKEND_URL || process.env.NEXT_PUBLIC_BACKEND_URL || '';
const content = `// Auto-generated during Vercel build
window.__ENV = {
  BACKEND_URL: "${backendUrl}"
};
`;

fs.writeFileSync(path.join(__dirname, 'env-config.js'), content);
console.log('✅ Injected Vercel environment variable BACKEND_URL:', backendUrl || '(none)');
