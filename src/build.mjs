// Сборка сайта: читает data/site.json и записывает готовые страницы.
// Запуск: node src/build.mjs [папка сайта]
import { readFile, writeFile, mkdir, rm } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { renderHome, renderAbout, renderContact, renderNotFound } from './render.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(process.argv[2] || path.join(here, '..'));
// Для предпросмотра вне хостинга ссылки между страницами ведут прямо на index.html.
const index = process.env.PREVIEW ? 'index.html' : '';
const data = JSON.parse(await readFile(path.join(root, 'data', 'site.json'), 'utf8'));

async function page(rel, html) {
  const file = path.join(root, rel);
  if (html == null) {            // страница отключена — файла быть не должно
    await rm(path.dirname(file), { recursive: true, force: true });
    return `- ${rel} (отключена)`;
  }
  await mkdir(path.dirname(file), { recursive: true });
  await writeFile(file, html);
  return `+ ${rel} (${Buffer.byteLength(html)} байт)`;
}

// В предпросмотре страница открывается внутри чужой рамки, поэтому строгая политика загрузки снимается.
const prep = (html) => (html && process.env.PREVIEW ? html.replace(/<meta http-equiv="Content-Security-Policy"[^>]*>\n/, '') : html);
const out = [];
await writeFile(path.join(root, 'index.html'), prep(renderHome(data, { base: '', index })));
out.push('+ index.html');
out.push(await page('about/index.html', prep(renderAbout(data, { base: '../', index }))));
out.push(await page('contact/index.html', prep(renderContact(data, { base: '../', index }))));
await writeFile(path.join(root, '404.html'), renderNotFound(data));
out.push('+ 404.html');
await writeFile(path.join(root, 'ping.txt'), 'ok\n');
await writeFile(path.join(root, '.nojekyll'), '');
await writeFile(path.join(root, 'robots.txt'), 'User-agent: *\nAllow: /\n');
console.log(out.join('\n'));
