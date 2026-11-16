// Временный предпросмотр варианта главной: node src/preview.mjs <папка> <ключ=значение для home>...
// Пример: node src/preview.mjs preview/listen-scroll listenLayout=scroll
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import { renderHome, setAssetVersion } from './render.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const [dir, ...pairs] = process.argv.slice(2);
const data = JSON.parse(await readFile(path.join(root, 'data', 'site.json'), 'utf8'));
for (const p of pairs) { const [k, v] = p.split('='); data.home[k] = v; }
const hash = createHash('sha1');
for (const f of ['assets/css/site.css', 'assets/css/noscript.css', 'assets/js/release.js', 'assets/js/scroller.js']) hash.update(await readFile(path.join(root, f)));
setAssetVersion(hash.digest('hex').slice(0, 10));
const base = '../'.repeat(dir.split('/').filter(Boolean).length);
const html = renderHome(data, { base })
  .replace('<meta property="og:type"', '<meta name="robots" content="noindex">\n<meta property="og:type"')
  .replace(/<link rel="canonical"[^>]*>\n/, '');
await mkdir(path.join(root, dir), { recursive: true });
await writeFile(path.join(root, dir, 'index.html'), html);
console.log('+', dir + '/index.html');
