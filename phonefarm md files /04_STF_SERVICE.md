# ⚙️ Step 04 — Create the STF Service

This is the Laravel class that talks to STF's API.
It fetches the phone info and stream URL so we can display it.

---

## Create the Services Folder

```bash
cd ~/phonefarm
mkdir -p app/Services
```

---

## Create the STFService Class

```bash
nano app/Services/STFService.php
```

Paste this entire file:

```php
<?php

namespace App\Services;

use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

class STFService
{
    private string $baseUrl;
    private string $token;

    public function __construct()
    {
        $this->baseUrl = config('services.stf.base_url');
        $this->token   = config('services.stf.token');
    }

    /**
     * Get all connected devices from STF
     */
    public function getDevices(): array
    {
        try {
            $response = Http::withToken($this->token)
                ->timeout(5)
                ->get("{$this->baseUrl}/api/v1/devices");

            if ($response->successful()) {
                return $response->json('devices') ?? [];
            }

            Log::error('STF getDevices failed', [
                'status' => $response->status(),
                'body'   => $response->body()
            ]);

            return [];

        } catch (\Exception $e) {
            Log::error('STF connection error: ' . $e->getMessage());
            return [];
        }
    }

    /**
     * Get a single device by its serial number
     */
    public function getDevice(string $serial): array
    {
        try {
            $response = Http::withToken($this->token)
                ->timeout(5)
                ->get("{$this->baseUrl}/api/v1/devices/{$serial}");

            if ($response->successful()) {
                return $response->json('device') ?? [];
            }

            return [];

        } catch (\Exception $e) {
            Log::error('STF getDevice error: ' . $e->getMessage());
            return [];
        }
    }

    /**
     * Get the first available connected device
     */
    public function getFirstDevice(): array
    {
        $devices = $this->getDevices();

        foreach ($devices as $device) {
            if ($device['present'] === true) {
                return $device;
            }
        }

        return [];
    }

    /**
     * Build the stream URL for a device
     * This is the URL we embed in the iframe
     */
    public function getStreamUrl(string $serial): string
    {
        return "{$this->baseUrl}/#!/control/{$serial}";
    }
}
```

Save: `Ctrl+X` → `Y` → `Enter`

---

## Add STF Config to config/services.php

```bash
nano config/services.php
```

At the bottom of the file, before the closing `];` add:

```php
'stf' => [
    'base_url' => env('STF_BASE_URL', 'http://localhost:7100'),
    'token'    => env('STF_TOKEN', ''),
],
```

Save the file.

---

## Clear Config Cache

```bash
php artisan config:clear
```

---

## Test the Service Works

Create a quick test route in `routes/web.php`:

```bash
nano routes/web.php
```

Add this temporary test route at the bottom:

```php
Route::get('/test-stf', function () {
    $stf = new \App\Services\STFService();
    $devices = $stf->getDevices();
    return response()->json($devices);
});
```

Save, then open browser:
```
http://localhost:8000/test-stf
```

You should see JSON with your phone details:
```json
[
  {
    "serial": "aece3bbd",
    "model": "M2101K6G",
    "present": true,
    "ready": true,
    "platform": "Android",
    "version": "12"
  }
]
```

✅ If you see your phone — the service works!

---

## Remove the Test Route

Once confirmed working, remove the test route from `routes/web.php`.
We'll add the real route in the next step.

---

## Checklist

- [ ] `app/Services/STFService.php` created
- [ ] STF config added to `config/services.php`
- [ ] `php artisan config:clear` run
- [ ] Test route returns phone JSON ✅
- [ ] Test route removed
