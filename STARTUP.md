# PhoneFarm v2 — Startup Guide

Run these steps in order every time the laptop restarts.

---

## 1. Start Docker Containers

```bash
docker start phonefarm-rethinkdb phonefarm-stf
```

Wait a few seconds for STF to fully boot.

---

## 2. Restart ADB (Bound to All Interfaces)

The STF Docker container needs ADB reachable on the network interface, not just localhost.

```bash
adb kill-server
adb -a nodaemon server start &
```

Verify the phone is visible:

```bash
adb devices
# Expected: aece3bbd   device
```

If the phone is not listed, unplug and replug the USB cable, then run `adb devices` again.

---

## 3. Start ngrok

```bash
ngrok start --all --config ~/.config/ngrok/ngrok.yml
```

Leave this terminal open, or run it in the background:

```bash
ngrok start --all --config ~/.config/ngrok/ngrok.yml > /tmp/ngrok.log 2>&1 &
```

Get the tunnel URLs:

```bash
curl -s http://localhost:4040/api/tunnels | python3 -c "
import sys, json
for t in json.load(sys.stdin).get('tunnels', []):
    print(f\"{t['name']:10} → {t['public_url']}\")
"
```

You will get two URLs — one for Laravel, one for STF. Note the **stf** URL for the next step.

---

## 4. Update the STF URL

ngrok issues a new URL every restart. Run the update script with the new STF URL from step 3:

```bash
cd ~/Projects/phonefarmv2
./scripts/update-ngrok-stf-url.sh https://<new-stf-url>.ngrok-free.app
```

This will:
- Update `STF_PUBLIC_BASE_URL` in `.env`
- Patch the URL inside the STF Docker container
- Restart the STF container
- Clear the Laravel config cache

---

## 5. Start Laravel

```bash
cd ~/Projects/phonefarmv2
php artisan serve --host=0.0.0.0 --port=8000
```

Or in the background:

```bash
php artisan serve --host=0.0.0.0 --port=8000 > /tmp/laravel.log 2>&1 &
```

---

## 6. Open the Dashboard

Use the **laravel** ngrok URL from step 3:

```
https://<laravel-url>.ngrok-free.app
```

Log in, select a phone from the dropdown, and the screen stream will appear.

---

## Summary Checklist

```
[ ] docker start phonefarm-rethinkdb phonefarm-stf
[ ] adb kill-server && adb -a nodaemon server start &
[ ] adb devices  →  phone listed
[ ] ngrok start --all --config ~/.config/ngrok/ngrok.yml
[ ] ./scripts/update-ngrok-stf-url.sh https://<stf-ngrok-url>
[ ] php artisan serve --host=0.0.0.0 --port=8000
[ ] Open https://<laravel-ngrok-url> in browser
```

---

## Troubleshooting

**Phone screen shows grey / "Try to reconnect"**
The minicap buffer deadlocked. Restart the STF container:
```bash
docker restart phonefarm-stf
```

**STF login page appears inside the phone iframe**
The ngrok URL changed and was not updated. Re-run step 4.

**`adb devices` shows no devices**
- Unplug and replug the USB cable
- Check USB debugging is still enabled on the phone
- Run `adb kill-server && adb -a nodaemon server start &` again

**Laravel shows "Vite manifest not found"**
The frontend assets need to be built:
```bash
cd ~/Projects/phonefarmv2
npm run build
rm -f public/hot
```

**Audio does not play**
Audio starts automatically when you select a phone. If it fails, check the log:
```bash
tail -f storage/logs/phone-audio.log
```
Make sure USB debugging is active and `adb devices` shows the phone.
