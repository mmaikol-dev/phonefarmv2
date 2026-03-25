# STF Touch Controls Fix

## Issue

The Laravel dashboard was able to show the STF phone screen, but taps and touch gestures did not work.

The screen stream was live, but the dashboard showed behavior like:

- the phone display rendered correctly
- touch input did nothing
- the browser console showed websocket errors for STF control

Typical errors seen in the browser console were:

```text
WebSocket connection to 'ws://127.0.0.1:7110/socket.io/?EIO=4&transport=websocket' failed: WebSocket is closed before the connection is established.
```

## Root Cause

This turned out to be a session and architecture problem, not just a missing click handler.

There were several layers to it:

1. The STF screen stream and STF touch controls use different connections.
   - Screen video came from the device display websocket like `ws://127.0.0.1:7400`
   - Touch control came from STF's Socket.IO websocket on port `7110`

2. The STF API token was not enough for touch control.
   - Laravel could call the STF REST API with `STF_TOKEN`
   - But STF websocket auth only accepted a browser session cookie with `req.session.jwt`

3. Our first custom Laravel-side touch implementation was trying to reproduce STF's native control flow across origins.
   - That made the control socket fragile
   - It depended on STF browser session bootstrap, websocket auth, and cookie scope behaving perfectly from inside the Laravel app shell

4. Host consistency mattered.
   - `localhost` and `127.0.0.1` are different cookie scopes
   - Mixing them broke STF browser session recognition

## What We Tried

We worked through the issue in stages.

### 1. Verified the screen stream

The raw device websocket was working, which proved STF could stream the device image into the dashboard.

### 2. Added custom touch support in Laravel

We built a custom `stf-screen-viewer.tsx` component that:

- rendered the raw screen stream on a canvas
- captured pointer events
- sent `input.touchDown`, `input.touchMove`, `input.touchUp`, and `input.touchCommit`

This matched STF's event names and payload shape.

### 3. Installed `socket.io-client`

STF websocket port `7110` does not serve the Socket.IO browser client script.

Requesting:

```text
http://127.0.0.1:7110/socket.io/socket.io.js
```

returned `400 Bad Request`, so we installed `socket.io-client` directly in the Laravel frontend instead.

### 4. Added device claim logic

We updated the dashboard flow so Laravel would claim the device before trying to control it.

That ensured STF considered the device "in use" by the current user.

### 5. Added STF browser session bootstrap

We discovered that STF websocket auth only checks the STF browser session cookie.

So we added a generated STF `?jwt=...` URL and loaded it in a hidden iframe before opening the control socket.

That was intended to create the STF browser session automatically.

### 6. Inspected STF source code directly

We checked the installed `@devicefarmer/stf` source and confirmed:

- control websocket auth only accepts `req.session.jwt`
- touch events were named correctly
- STF's own frontend opens the control socket from the STF app itself
- STF has a standalone control route:

```text
#!/c/<serial>?standalone
```

## Final Fix

Instead of continuing to reimplement STF touch handling in Laravel, we switched to embedding STF's own standalone control page inside the dashboard phone frame.

That solved the problem because:

- STF's own page already knows how to connect to its control websocket
- STF's own page already handles touch and pointer events correctly
- we no longer needed to maintain a fragile custom touch bridge

## Code Changes Made

### 1. Use STF standalone control route

We changed the device stream URL generation in:

- [STFService.php](/home/atlas/PHONE%20FARM/phonefarmv2/app/Services/STFService.php)

From the full control page:

```text
#!/control/<serial>
```

to the standalone route:

```text
#!/c/<serial>?standalone
```

### 2. Embed STF standalone view in the dashboard

We updated:

- [dashboard.tsx](/home/atlas/PHONE%20FARM/phonefarmv2/resources/js/pages/dashboard.tsx)

So the phone shell now renders:

- a hidden STF session bootstrap iframe
- the STF standalone control page iframe

instead of the custom raw-screen touch viewer.

## Environment Settings Required

The working setup depends on using `127.0.0.1` consistently.

The important `.env` values are:

```env
APP_URL=http://127.0.0.1:8000
STF_BASE_URL=http://127.0.0.1:7100
STF_WEBSOCKET_URL=http://127.0.0.1:7110
STF_WEBSOCKET_PORT=7110
STF_AUTH_SECRET="kute kittykat"
STF_TOKEN=<YOUR_VALID_STF_TOKEN>
```

After changing `.env`, clear config:

```bash
cd /home/atlas/PHONE\ FARM/phonefarmv2
php artisan config:clear
```

## Verification

After the final change, the dashboard used STF's native standalone control view and touch controls worked.

Checks also passed:

```bash
php artisan test --compact tests/Feature/DashboardTest.php
npm run types:check
vendor/bin/pint --dirty --format agent
```

## Summary

The real issue was that touch input in STF is not just "send clicks over websocket".

It depends on:

- STF browser-session auth
- correct cookie scope
- correct control websocket behavior
- STF's own frontend control flow

The stable fix was to stop reimplementing STF touch control in Laravel and instead embed STF's standalone control route inside the Laravel dashboard.
