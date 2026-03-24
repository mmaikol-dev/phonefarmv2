# 🖥️ Step 05 — Controller, Route & View

This is where we build the actual page that shows the phone.

---

## Create the Controller

```bash
cd ~/phonefarm
php artisan make:controller PhoneController
```

Now open it:
```bash
nano app/Http/Controllers/PhoneController.php
```

Replace the entire contents with:

```php
<?php

namespace App\Http\Controllers;

use App\Services\STFService;

class PhoneController extends Controller
{
    public function __construct(private STFService $stf) {}

    public function show()
    {
        // Get the first connected phone from STF
        $device = $this->stf->getFirstDevice();

        // If no phone found, show error page
        if (empty($device)) {
            return view('phone', [
                'error'     => 'No phone connected. Make sure STF is running and phone is plugged in.',
                'device'    => null,
                'streamUrl' => null,
            ]);
        }

        // Build the stream URL for this phone
        $streamUrl = $this->stf->getStreamUrl($device['serial']);

        return view('phone', [
            'error'     => null,
            'device'    => $device,
            'streamUrl' => $streamUrl,
        ]);
    }
}
```

Save: `Ctrl+X` → `Y` → `Enter`

---

## Add the Route

```bash
nano routes/web.php
```

Replace the entire contents with:

```php
<?php

use Illuminate\Support\Facades\Route;
use App\Http\Controllers\PhoneController;

Route::get('/', [PhoneController::class, 'show']);
```

Save the file.

---

## Create the View

```bash
nano resources/views/phone.blade.php
```

Paste this entire file:

```blade
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PhoneFarm — Virtual Phone</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            background: #0f172a;
            color: #f1f5f9;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .container {
            display: flex;
            gap: 40px;
            align-items: flex-start;
            padding: 40px;
        }

        /* Phone Frame */
        .phone-frame {
            background: #1e293b;
            border-radius: 40px;
            padding: 16px;
            box-shadow: 0 0 0 2px #334155, 0 25px 60px rgba(0,0,0,0.5);
            position: relative;
        }

        .phone-frame::before {
            content: '';
            display: block;
            width: 60px;
            height: 6px;
            background: #334155;
            border-radius: 3px;
            margin: 0 auto 12px;
        }

        .phone-screen {
            width: 360px;
            height: 640px;
            border-radius: 24px;
            overflow: hidden;
            background: #000;
            position: relative;
        }

        .phone-screen iframe {
            width: 100%;
            height: 100%;
            border: none;
        }

        /* Error state */
        .phone-error {
            width: 360px;
            height: 640px;
            border-radius: 24px;
            background: #0f172a;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 16px;
            padding: 32px;
            text-align: center;
        }

        .phone-error .icon {
            font-size: 48px;
        }

        .phone-error p {
            color: #94a3b8;
            line-height: 1.6;
            font-size: 14px;
        }

        /* Info Panel */
        .info-panel {
            width: 280px;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }

        .info-panel h1 {
            font-size: 24px;
            font-weight: 700;
            color: #f1f5f9;
        }

        .info-panel h1 span {
            color: #3b82f6;
        }

        .card {
            background: #1e293b;
            border-radius: 12px;
            padding: 16px;
            border: 1px solid #334155;
        }

        .card-title {
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: #64748b;
            margin-bottom: 12px;
        }

        .info-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 0;
            border-bottom: 1px solid #334155;
            font-size: 13px;
        }

        .info-row:last-child {
            border-bottom: none;
        }

        .info-row .label {
            color: #64748b;
        }

        .info-row .value {
            color: #f1f5f9;
            font-weight: 500;
        }

        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 10px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 600;
        }

        .status-online {
            background: #052e16;
            color: #4ade80;
            border: 1px solid #166534;
        }

        .status-offline {
            background: #1c0a0a;
            color: #f87171;
            border: 1px solid #7f1d1d;
        }

        .dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: currentColor;
        }

        .hint {
            background: #1e3a5f;
            border: 1px solid #1d4ed8;
            border-radius: 10px;
            padding: 12px 16px;
            font-size: 13px;
            color: #93c5fd;
            line-height: 1.6;
        }

        .hint strong {
            color: #bfdbfe;
        }
    </style>
</head>
<body>

<div class="container">

    {{-- Phone Frame --}}
    <div class="phone-frame">
        <div class="phone-screen">

            @if($error)
                {{-- Error State --}}
                <div class="phone-error">
                    <div class="icon">📵</div>
                    <p>{{ $error }}</p>
                </div>

            @else
                {{-- Live Phone Stream --}}
                <iframe
                    src="{{ $streamUrl }}"
                    allow="microphone; camera"
                    allowfullscreen>
                </iframe>
            @endif

        </div>
    </div>

    {{-- Info Panel --}}
    <div class="info-panel">

        <h1>Phone<span>Farm</span></h1>

        @if($device)
            {{-- Device Status --}}
            <div class="card">
                <div class="card-title">Device Status</div>

                <div class="info-row">
                    <span class="label">Status</span>
                    <span class="status-badge status-online">
                        <span class="dot"></span> Live
                    </span>
                </div>

                <div class="info-row">
                    <span class="label">Model</span>
                    <span class="value">{{ $device['model'] ?? 'Unknown' }}</span>
                </div>

                <div class="info-row">
                    <span class="label">Android</span>
                    <span class="value">{{ $device['version'] ?? '—' }}</span>
                </div>

                <div class="info-row">
                    <span class="label">Serial</span>
                    <span class="value" style="font-family: monospace; font-size: 11px;">
                        {{ $device['serial'] ?? '—' }}
                    </span>
                </div>

                <div class="info-row">
                    <span class="label">Platform</span>
                    <span class="value">{{ $device['platform'] ?? '—' }}</span>
                </div>
            </div>

            {{-- Hint --}}
            <div class="hint">
                <strong>💡 Tip:</strong> Click anywhere on the phone screen
                to interact. You can tap, swipe, and type just like a real phone.
            </div>

        @else
            {{-- No Device --}}
            <div class="card">
                <div class="card-title">Device Status</div>
                <div class="info-row">
                    <span class="label">Status</span>
                    <span class="status-badge status-offline">
                        <span class="dot"></span> Offline
                    </span>
                </div>
            </div>

            <div class="hint">
                <strong>To connect a phone:</strong><br>
                1. Run <code>docker start rethinkdb</code><br>
                2. Run <code>stf local --public-ip 127.0.0.1</code><br>
                3. Plug in your phone via USB<br>
                4. Refresh this page
            </div>
        @endif

    </div>

</div>

</body>
</html>
```

Save: `Ctrl+X` → `Y` → `Enter`

---

## Checklist

- [ ] `PhoneController.php` created and filled
- [ ] `routes/web.php` updated
- [ ] `resources/views/phone.blade.php` created
