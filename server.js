const express = require('express');
const { spawn } = require('child_process');
const path = require('path');

const app = express();
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

app.post('/api/chat', (req, res) => {
  const { message } = req.body;
  if (!message) return res.status(400).json({ error: 'message required' });

  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.flushHeaders();

  const send = (type, data) =>
    res.write(`data: ${JSON.stringify({ type, data })}\n\n`);

  const pythonBin = process.platform === 'win32'
    ? '.venv\\Scripts\\python.exe'
    : '.venv/bin/python';
  const py = spawn(pythonBin, [path.join(__dirname, 'api.py'), message], {
    env: { ...process.env },
    cwd: __dirname,
  });

  console.log('[spawning python] pid:', py.pid);

  py.on('error', (err) => console.error('[spawn error]', err));

  py.stdout.on('data', (chunk) => {
    const text = chunk.toString();
    console.log('[stdout]', JSON.stringify(text));
    const clean = text.split('\n')
      .filter(l =>
        !l.startsWith('GOOGLE_API_KEY') &&
        !l.startsWith('[Gemini]') &&
        !l.startsWith('[Mistral]') &&
        !l.includes('mcp_use') &&
        !l.match(/^\s*"error"\s*:/) &&
        !l.match(/^\s*"timestamp"\s*:/) &&
        !l.match(/^\s*[{}]\s*$/) &&
        l.trim()
      )
      .join('\n').trim();
    if (clean) send('token', clean);
  });

  py.stderr.on('data', (data) => {
    const msg = data.toString();
    console.log('[stderr]', msg); // keep for debugging
    // don't send stderr to frontend
  });

  py.on('close', (code) => {
    console.log('[close] code:', code);
    send('done', '');
    res.end();
  });

// req.on('close', () => {
//   if (!res.writableEnded) py.kill();
// });
});

app.get('/health', (_req, res) => res.json({ status: 'ok' }));

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`MCP Chat running on http://localhost:${PORT}`));