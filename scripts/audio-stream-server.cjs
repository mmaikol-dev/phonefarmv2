#!/usr/bin/env node
/**
 * Phone audio HTTP streaming server.
 *
 * Spawns scrcpy to capture Android audio, outputs Ogg/Opus, and serves it as
 * a chunked HTTP response so the browser <audio> element can play it directly.
 *
 * Listens on 127.0.0.1:AUDIO_PORT (default 7201).
 * Poorxy proxies /audio → this server so it is reachable via the STF ngrok URL.
 *
 * Usage (via start-phone-audio.sh):
 *   ANDROID_SERIAL=<serial> SCRCPY_AUDIO_SOURCE=output node audio-stream-server.js
 */

'use strict';

const http = require('http');
const path = require('path');
const { spawn } = require('child_process');

const ROOT_DIR     = path.join(__dirname, '..');
const SCRCPY_BIN   = path.join(ROOT_DIR, 'tools', 'scrcpy-v3.3.4', 'scrcpy');
const PORT         = parseInt(process.env.AUDIO_PORT || '7201', 10);
const SERIAL       = process.env.ANDROID_SERIAL || '';
const AUDIO_SOURCE = process.env.SCRCPY_AUDIO_SOURCE || 'output';

// ------------------------------------------------------------------
// Ogg page parser — we need to identify the two header pages
// (OpusHead + OpusTags) so that late-joining clients receive them.
// ------------------------------------------------------------------
const OGG_MAGIC = Buffer.from('OggS');
let headerBuf    = Buffer.alloc(0); // captured Ogg header pages
let headerReady  = false;           // true once both Opus header pages captured
let headerCount  = 0;

/**
 * Parse complete Ogg pages out of `buf`, invoking `onPage` for each.
 * Returns the number of bytes consumed (the caller should keep the rest).
 */
function parseOggPages(buf, onPage) {
    let offset = 0;
    while (offset + 27 <= buf.length) {
        if (!buf.slice(offset, offset + 4).equals(OGG_MAGIC)) break;

        const numSegments = buf[offset + 26];
        if (offset + 27 + numSegments > buf.length) break;

        let pageSize = 27 + numSegments;
        for (let i = 0; i < numSegments; i++) pageSize += buf[offset + 27 + i];
        if (offset + pageSize > buf.length) break;

        onPage(buf.slice(offset, offset + pageSize));
        offset += pageSize;
    }
    return offset;
}

// ------------------------------------------------------------------
// Active HTTP response objects — one per connected browser tab
// ------------------------------------------------------------------
const clients = new Set();

function broadcast(chunk) {
    for (const res of clients) {
        try {
            res.write(chunk);
        } catch (_) {
            clients.delete(res);
        }
    }
}

// ------------------------------------------------------------------
// Spawn scrcpy
// ------------------------------------------------------------------
const scrcpyArgs = [
    '--no-video',
    '--no-window',
    '--audio-source', AUDIO_SOURCE,
    '--audio-codec',  'opus',
    '--record',       '-',
    '--record-format','opus',
];

const env = Object.assign({}, process.env);
if (SERIAL) env.ANDROID_SERIAL = SERIAL;

console.log(`[audio] starting scrcpy  serial=${SERIAL || '(any)'}  source=${AUDIO_SOURCE}`);

const scrcpy = spawn(SCRCPY_BIN, scrcpyArgs, {
    env,
    stdio: ['ignore', 'pipe', 'pipe'],
});

scrcpy.stderr.on('data', d => process.stderr.write(d));

scrcpy.on('exit', (code, signal) => {
    console.error(`[audio] scrcpy exited  code=${code}  signal=${signal}`);
    process.exit(typeof code === 'number' ? code : 1);
});

// Kill scrcpy when this process is terminated
process.on('SIGTERM', () => { scrcpy.kill('SIGTERM'); process.exit(0); });
process.on('SIGINT',  () => { scrcpy.kill('SIGTERM'); process.exit(0); });

let remainder = Buffer.alloc(0);

scrcpy.stdout.on('data', chunk => {
    const data     = Buffer.concat([remainder, chunk]);
    const consumed = parseOggPages(data, page => {
        // Collect the first 2 Ogg pages: OpusHead + OpusTags
        if (!headerReady) {
            headerBuf = Buffer.concat([headerBuf, page]);
            headerCount++;
            if (headerCount >= 2) {
                headerReady = true;
                console.log('[audio] Opus header captured — streaming active');
            }
        }
        broadcast(page);
    });
    remainder = data.slice(consumed);
});

// ------------------------------------------------------------------
// HTTP server
// ------------------------------------------------------------------
const server = http.createServer((req, res) => {
    if (req.method === 'OPTIONS') {
        res.writeHead(204, {
            'Access-Control-Allow-Origin':  '*',
            'Access-Control-Allow-Methods': 'GET',
        });
        res.end();
        return;
    }

    if (req.method !== 'GET') { res.writeHead(405); res.end(); return; }

    res.writeHead(200, {
        'Content-Type':      'audio/ogg; codecs=opus',
        'Cache-Control':     'no-cache, no-store, must-revalidate',
        'X-Accel-Buffering': 'no',          // disable nginx buffering if present
        'Access-Control-Allow-Origin': '*',
    });
    // Flush HTTP headers immediately so the client doesn't wait for the first
    // audio chunk (which only arrives once the phone plays audio).
    res.flushHeaders();

    // Send cached Opus header pages so the browser can decode from the start
    if (headerBuf.length > 0) res.write(headerBuf);

    clients.add(res);
    console.log(`[audio] client connected  total=${clients.size}`);

    const cleanup = () => {
        clients.delete(res);
        console.log(`[audio] client disconnected  total=${clients.size}`);
    };
    req.on('close',  cleanup);
    req.on('error',  cleanup);
    res.on('error',  cleanup);
    res.on('finish', cleanup);
});

// Listen on all interfaces so the STF Docker container can reach us via
// host.docker.internal (which resolves to the Docker bridge IP, not 127.0.0.1).
server.listen(PORT, '0.0.0.0', () => {
    console.log(`[audio] HTTP stream ready at http://0.0.0.0:${PORT}/`);
});
