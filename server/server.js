const express = require('express');
const { marked } = require('marked');
const fs = require('fs');
const path = require('path');
const os = require('os');

const app = express();
const PORT = process.env.PORT || 3000;
const BOOK_DIR = path.join(__dirname, 'book');

app.use('/static', express.static(path.join(__dirname, 'public')));
app.use('/game', express.static(path.join(__dirname, 'game')));
app.use('/v2', express.static(path.join(__dirname, 'v2')));

// Главная — список эпизодов
app.get('/', (req, res) => {
  const files = fs.readdirSync(BOOK_DIR)
    .filter(f => f.endsWith('.md'))
    .sort();

  const episodes = files.map(f => {
    const content = fs.readFileSync(path.join(BOOK_DIR, f), 'utf-8');
    const firstLine = content.split('\n').find(l => l.startsWith('#')) || f;
    const title = firstLine.replace(/^#+\s*/, '');
    const slug = f.replace('.md', '');
    return { slug, title, filename: f };
  });

  const html = fs.readFileSync(path.join(__dirname, 'views', 'index.html'), 'utf-8')
    .replace('{{EPISODES}}', episodes.map(ep =>
      `<a href="/ep/${ep.slug}" class="episode-link">
        <span class="episode-num">${ep.slug.replace('ep_', '№')}</span>
        <span class="episode-title">${ep.title}</span>
      </a>`
    ).join('\n'));

  res.send(html);
});

// Страница эпизода
app.get('/ep/:slug', (req, res) => {
  const slug = req.params.slug;
  const filePath = path.join(BOOK_DIR, slug + '.md');

  if (!fs.existsSync(filePath)) {
    return res.status(404).send('Эпизод не найден');
  }

  const md = fs.readFileSync(filePath, 'utf-8');
  const htmlContent = marked(md);

  // Навигация
  const files = fs.readdirSync(BOOK_DIR).filter(f => f.endsWith('.md')).sort();
  const idx = files.indexOf(slug + '.md');
  const prev = idx > 0 ? files[idx - 1].replace('.md', '') : null;
  const next = idx < files.length - 1 ? files[idx + 1].replace('.md', '') : null;

  const template = fs.readFileSync(path.join(__dirname, 'views', 'episode.html'), 'utf-8');

  const html = template
    .replace('{{CONTENT}}', htmlContent)
    .replace('{{PREV}}', prev ? `<a href="/ep/${prev}" class="nav-btn">← Предыдущий</a>` : '<span></span>')
    .replace('{{NEXT}}', next ? `<a href="/ep/${next}" class="nav-btn">Следующий →</a>` : '<span></span>')
    .replace('{{SLUG}}', slug);

  res.send(html);
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`\n  Сервер запущен:\n`);
  console.log(`  Локально:  http://localhost:${PORT}`);

  // Показать IP для доступа из локальной сети
  const nets = os.networkInterfaces();
  for (const name of Object.keys(nets)) {
    for (const net of nets[name]) {
      if (net.family === 'IPv4' && !net.internal) {
        console.log(`  Wi-Fi:     http://${net.address}:${PORT}`);
      }
    }
  }
  console.log();
});
