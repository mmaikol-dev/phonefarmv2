# STF Remote Access — What We Fixed and How

This document covers every problem encountered making the STF phone screen visible inside the Laravel dashboard for remote users (via ngrok), and exactly how each was resolved.

---

## Overview

**Goal:** Remote users access the Laravel dashboard through ngrok and see a live Android phone screen streamed via OpenSTF — without ever seeing the STF login page.

**Stack:** Laravel 13 + Inertia/React + OpenSTF (Docker) + ngrok free tier

---

## Problem 1 — `npm run dev` Bus Error

**Symptom:** Running `npm run dev` crashed with a Bus error.

**Cause:** Node v16 was active but the project's native binaries (rollup, lightningcss) were compiled for Node v24.

**Fix:**
```bash
nvm use 24
rm -rf node_modules && npm install
npm run build   # use build instead of dev for public access
rm public/hot   # remove the hot file so Laravel uses the built assets
```

---

## Problem 2 — STF Not Detecting the Phone

**Symptom:** STF API returned no devices.

**Cause:** The ADB daemon was bound to `127.0.0.1` only, so the STF Docker container couldn't reach it via `host.docker.internal`.

**Fix:**
```bash
adb kill-server
adb -a nodaemon server start &   # bind to all interfaces
```

The Docker container was already started with `--adb-host host.docker.internal --adb-port 5037`.

---

## Problem 3 — Two ngrok Agents Kicked Each Other Out

**Symptom:** Accessing either the Laravel or STF ngrok URL returned `ERR_NGROK_3200` (session limit exceeded).

**Cause:** ngrok free tier allows only one agent session. Running a second `ngrok` process killed the first.

**Fix:** Combined both tunnels in one ngrok config file (`~/.config/ngrok/ngrok.yml`):

```yaml
version: "3"
agent:
    authtoken: <your-token>
tunnels:
    laravel:
        proto: http
        addr: 8000
    stf:
        proto: http
        addr: 7100
```

Start with: `ngrok start --all`

---

## Problem 4 — Vite Manifest Not Found via ngrok

**Symptom:** Laravel threw "Vite manifest not found" when accessed through ngrok.

**Cause:** `npm run dev` was running and had created `public/hot`, pointing Laravel at the local Vite dev server instead of built assets.

**Fix:**
```bash
npm run build
rm public/hot
```

---

## Problem 5 — STF Login Page Showing in the Dashboard iframe

**Symptom:** The phone screen iframe showed the STF login page instead of the device stream.

**Cause 1:** `STF_BASE_URL` was set to the ngrok URL, so server-side API calls went through ngrok and got blocked.

**Cause 2:** The session cookie STF sets after login has `SameSite=Lax` by default, which browsers block in cross-origin iframes.

**Cause 3:** Cookies with `secure: true` require HTTPS, but STF's Express apps weren't configured to trust the proxy (`X-Forwarded-Proto` from ngrok).

### Fix A — Split STF URLs into server-side vs browser-facing

**.env:**
```
STF_BASE_URL=http://127.0.0.1:7100        # server-side API calls (local)
STF_PUBLIC_BASE_URL=https://<stf-ngrok>   # what browsers navigate to
```

**config/services.php** — added `public_base_url`:
```php
'stf' => [
    'base_url'        => env('STF_BASE_URL', ''),
    'public_base_url' => env('STF_PUBLIC_BASE_URL', ''),
    'token'           => env('STF_TOKEN', ''),
    'auth_secret'     => env('STF_AUTH_SECRET', ''),
    'websocket_port'  => env('STF_WEBSOCKET_PORT', 7110),
],
```

**STFService.php** — `getBaseUrl()` returns public URL for browsers, `$baseUrl` used only for API calls.

### Fix B — Patch STF Docker container cookies (`SameSite=none; Secure`)

Applied to `/app/lib/units/auth/mock.js`, `app/index.js`, and `api/index.js` inside the container:

```js
app.set('trust proxy', true)

app.use(cookieSession({
    name: options.ssid,
    sameSite: 'none',    // allow cross-origin iframe
    secure: true,        // required with SameSite=none
    keys: [options.secret]
}))
```

---

## Problem 6 — JWT Authentication (Silent Login in Hidden iframe)

**Symptom:** Remote users saw the STF login page even after being logged into the Laravel app.

**Goal:** The dashboard must silently authenticate the user into STF without them interacting with STF directly.

**Approach:** Generate a signed JWT in PHP and load it in a hidden iframe. STF's app middleware accepts `?jwt=TOKEN` and sets a session cookie.

**STF's non-standard JWT format** (critical detail): STF's `jwtutil.js` reads `exp` from `decoded.header.exp`, not `decoded.payload.exp`.

**STFService.php — `getBrowserSessionBootstrapUrl()`:**
```php
$header = [
    'alg' => 'HS256',
    'exp' => (int) round(microtime(true) * 1000) + 86_400_000, // exp in HEADER
];
$payload = [
    'email' => $email,
    'name'  => $name,
];
// Standard HMAC-SHA256 signing, base64url encoded
return "{$this->publicBaseUrl}/?jwt={$encoded}";
```

**dashboard.tsx — bootstrap iframe with 5s fallback:**
```tsx
const [sessionReady, setSessionReady] = useState(!stfSessionUrl);

useEffect(() => {
    setSessionReady(!stfSessionUrl);
    if (stfSessionUrl) {
        sessionTimerRef.current = setTimeout(() => setSessionReady(true), 5000);
    }
}, [stfSessionUrl]);

// Hidden iframe authenticates silently
{stfSessionUrl && !sessionReady ? (
    <iframe src={stfSessionUrl} className="hidden"
        onLoad={() => setSessionReady(true)} />
) : null}
```

---

## Problem 7 — Screen WebSocket Not Reachable Remotely ("Try to Reconnect")

**Symptom:** The STF standalone device view showed "Try to reconnect" for remote users.

**Root cause:** STF's device screen WebSocket ran on port 7400 on `127.0.0.1` only. Remote browsers could not reach it. Using a separate ngrok tunnel for port 7400 failed because ngrok's interstitial can't be dismissed on a WebSocket-only server.

**Fix:** Proxy the screen WebSocket through poorxy (port 7100, already tunnelled via ngrok).

### Step 1 — Update `screen-ws-url-pattern`

In `/app/lib/cli/local/index.js` inside the container, changed the default from `ws://localhost:{port}` to:
```js
'wss://<stf-ngrok>/screen-ws'
```

This makes STF tell devices (via the API) that `display.url = wss://<stf-ngrok>/screen-ws`.

### Step 2 — Add WebSocket proxy in poorxy

In `/app/lib/units/poorxy/index.js`:
```js
server.on('upgrade', function(req, socket, head) {
    if (req.url === '/screen-ws' || req.url.startsWith('/screen-ws/')) {
        // Device screen stream (minicap frames)
        proxy.ws(req, socket, head, { target: 'ws://127.0.0.1:7400' })
    } else if (req.url.startsWith('/socket.io/')) {
        // Control WebSocket (touch, input)
        proxy.ws(req, socket, head, { target: options.websocketUrl })
    } else {
        socket.destroy()
    }
})
```

Also added HTTP route for socket.io polling:
```js
app.all('/socket.io/*', function(req, res) {
    proxy.web(req, res, { target: options.websocketUrl })
})
```

---

## Problem 8 — Control WebSocket Not Reachable Remotely (Touch/Input Broken)

**Symptom:** Screen showed but touch input didn't work. The socket.io control channel was hardcoded to `http://127.0.0.1:7110/` which is unreachable remotely.

**Fix:** Changed the app server's `--websocket-url` to the public ngrok URL in `/app/lib/cli/local/index.js`:
```js
, '--websocket-url', argv.websocketUrl || 'https://<stf-ngrok>/'
```

The browser now connects socket.io to the ngrok URL → poorxy → port 7110 (websocket unit).

---

## Problem 9 — Grey Screen (minicap Buffer Deadlock)

**Symptom:** Everything connected (101 WebSocket status, session cookie set) but the phone screen was solid grey.

**Root cause (discovered by protocol inspection):** The STF screen WebSocket at port 7400 uses a custom protocol. The client must send the string `"on"` after connecting to start receiving frames. The frame producer only runs while at least one client is subscribed. When all clients disconnect, the producer stops and minicap's socket buffer fills up. When the next client connects and sends "on", the producer tries to restart but minicap is stuck in `sock_alloc_send_pskb` (blocked waiting to write to a full buffer). No frames flow.

**Fix:** Restart the STF container to reset the minicap connection cleanly:
```bash
docker restart phonefarm-stf
```

**Permanent fix:** This will recur whenever all browser sessions disconnect and the buffer fills. The real fix is a watchdog, but for now a restart clears it.

---

## Preserving Container Changes

All patches above are made inside the running container. After each set of changes:
```bash
docker commit phonefarm-stf phonefarm-stf-local
```

This saves the state to the `phonefarm-stf-local` image so patches survive container recreation.

---

## When the ngrok URL Changes

ngrok free tier issues a new URL every time the agent restarts. Run:
```bash
./scripts/update-ngrok-stf-url.sh
```

This script:
1. Reads the new STF tunnel URL from ngrok's local API
2. Updates `STF_PUBLIC_BASE_URL` in `.env`
3. Patches `screen-ws-url-pattern` and `websocket-url` inside the container
4. Restarts STF

---

## Final Architecture

```
Browser
  │
  ├─ https://<laravel-ngrok>/dashboard
  │     Laravel app (port 8000)
  │     ├─ generates JWT bootstrap URL
  │     └─ serves stream iframe URL: https://<stf-ngrok>/#!/c/{serial}?standalone
  │
  └─ https://<stf-ngrok>/   ──► ngrok ──► poorxy (port 7100)
        ├─ GET /?jwt=TOKEN        ──► app server (7105): sets session cookie
        ├─ GET /api/*             ──► api server (7106)
        ├─ GET /auth/*            ──► auth-mock (7120)
        ├─ WS  /screen-ws         ──► screen WS server (7400): minicap JPEG frames
        └─ WS  /socket.io/        ──► websocket unit (7110): touch/control events
```
