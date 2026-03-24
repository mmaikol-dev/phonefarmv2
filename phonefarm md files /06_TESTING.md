# 🧪 Step 06 — Run & Test

## Full Startup Sequence

You need 3 things running at the same time.
Open 3 separate terminal tabs.

### Terminal 1 — RethinkDB
```bash
docker start rethinkdb
```

### Terminal 2 — STF
```bash
nvm use 18
stf local --public-ip 127.0.0.1
```
Wait until you see: `INF/poorxy [*] Listening on port 7100`

### Terminal 3 — Laravel
```bash
cd ~/phonefarm
php artisan serve
```

---

## Open the App

Go to:
```
http://localhost:8000
```

You should see:
- A dark UI with a phone frame on the left
- Your Redmi Note 10 Pro streaming live inside the frame
- Device info panel on the right (model, Android version, serial)

---

## Test Interactions

Try these from the browser:

| Action | How |
|--------|-----|
| Tap an app | Click on it in the phone screen |
| Swipe | Click and drag |
| Go home | Tap the home button on the phone |
| Open dialer | Tap the phone/dialer icon |
| Type text | Click a text field, type on your keyboard |

---

## Common Problems & Fixes

### Problem: Phone screen shows but is blank/black
**Cause:** STF is still initializing the phone stream
**Fix:** Wait 10–15 seconds and refresh the page

---

### Problem: Page loads but shows "No phone connected"
**Cause:** STF doesn't see the phone yet
**Fix:**
```bash
adb kill-server
adb start-server
adb devices
```
Then refresh the page.

---

### Problem: Page shows Laravel error — "Target class STFService does not exist"
**Cause:** Config cache not cleared after changes
**Fix:**
```bash
php artisan config:clear
php artisan cache:clear
```

---

### Problem: iframe loads but shows STF login page instead of phone
**Cause:** STF token is wrong or expired
**Fix:** Generate a new token (see Step 03) and update `.env`
```bash
php artisan config:clear
```

---

### Problem: "Connection refused" error in browser
**Cause:** Laravel is not running
**Fix:** Make sure `php artisan serve` is running in a terminal

---

### Problem: Phone shows in STF (localhost:7100) but not in Laravel
**Cause:** The stream URL format may differ for your STF version
**Fix:** Open STF at `http://localhost:7100`, click "Use" on your phone,
copy the URL from the browser address bar.
Then update `getStreamUrl()` in `STFService.php` to match that URL format.

---

## What Success Looks Like

```
✅ http://localhost:8000 loads
✅ Phone frame visible with dark UI
✅ Phone screen streaming live inside frame
✅ Clicking on phone screen controls the real phone
✅ Info panel shows correct device model and Android version
```

---

## Quick Restart Cheatsheet

If anything stops working:

```bash
# Restart RethinkDB
docker restart rethinkdb

# Restart STF (Ctrl+C first, then)
stf local --public-ip 127.0.0.1

# Restart Laravel (Ctrl+C first, then)
cd ~/phonefarm && php artisan serve

# Reset phone connection
adb kill-server && adb start-server
```
