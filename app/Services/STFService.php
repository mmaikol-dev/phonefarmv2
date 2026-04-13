<?php

namespace App\Services;

use Illuminate\Http\Client\PendingRequest;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Str;

class STFService
{
    private string $baseUrl;

    private string $publicBaseUrl;

    private string $token;

    public function __construct()
    {
        $this->baseUrl = rtrim((string) config('services.stf.base_url', ''), '/');
        $publicUrl = rtrim((string) config('services.stf.public_base_url', ''), '/');
        $this->publicBaseUrl = $publicUrl !== '' ? $publicUrl : $this->baseUrl;
        $this->token = (string) config('services.stf.token', '');
    }

    public function getBaseUrl(): string
    {
        return $this->publicBaseUrl;
    }

    public function getControlSocketUrl(): string
    {
        $configuredUrl = (string) config('services.stf.websocket_url', '');

        if ($configuredUrl !== '') {
            return rtrim($configuredUrl, '/').'/';
        }

        if ($this->baseUrl === '') {
            return '';
        }

        $parts = parse_url($this->baseUrl);

        if (! isset($parts['scheme'], $parts['host'])) {
            return '';
        }

        $port = config('services.stf.websocket_port', 7110);

        return "{$parts['scheme']}://{$parts['host']}:{$port}/";
    }

    public function getBrowserSessionBootstrapUrl(): ?string
    {
        if (! $this->isConfigured()) {
            return null;
        }

        $user = $this->getCurrentUser();

        if ($user === null) {
            return null;
        }

        $email = (string) ($user['email'] ?? '');

        if ($email === '') {
            return null;
        }

        $secret = (string) config('services.stf.auth_secret', 'kute kittykat');
        $name = (string) ($user['name'] ?? 'PhoneFarm');
        // STF's jwtutil reads exp from the header (non-standard but STF-specific)
        $header = [
            'alg' => 'HS256',
            'exp' => (int) round(microtime(true) * 1000) + 86_400_000,
        ];
        $payload = [
            'email' => $email,
            'name' => $name,
        ];

        $encodedHeader = $this->base64UrlEncode(json_encode($header, JSON_THROW_ON_ERROR));
        $encodedPayload = $this->base64UrlEncode(json_encode($payload, JSON_THROW_ON_ERROR));
        $signature = hash_hmac('sha256', "{$encodedHeader}.{$encodedPayload}", $secret, true);
        $encodedSignature = $this->base64UrlEncode($signature);

        return "{$this->publicBaseUrl}/?jwt={$encodedHeader}.{$encodedPayload}.{$encodedSignature}";
    }

    public function isConfigured(): bool
    {
        return $this->baseUrl !== '' && $this->token !== '';
    }

    public function getConfigurationError(): ?string
    {
        if ($this->baseUrl === '') {
            return 'Set STF_BASE_URL in your .env file before opening the live phone dashboard.';
        }

        if ($this->token === '') {
            return 'Set STF_TOKEN in your .env file so Laravel can talk to the STF API.';
        }

        return null;
    }

    /**
     * @return array<int, array<string, mixed>>
     */
    public function getDevices(): array
    {
        if (! $this->isConfigured()) {
            return [];
        }

        try {
            $response = $this->apiRequest()->get("{$this->baseUrl}/api/v1/devices");

            if ($response->successful()) {
                return $response->json('devices') ?? [];
            }

            Log::warning('STF device list request failed.', [
                'status' => $response->status(),
                'body' => $response->body(),
            ]);
        } catch (\Throwable $exception) {
            Log::warning('STF device list request threw an exception.', [
                'message' => $exception->getMessage(),
            ]);
        }

        return [];
    }

    public function claimDevice(string $serial): bool
    {
        if (! $this->isConfigured()) {
            return false;
        }

        try {
            $response = $this->apiRequest()->post("{$this->baseUrl}/api/v1/user/devices/{$serial}");

            return $response->successful();
        } catch (\Throwable $exception) {
            Log::warning('STF device claim request threw an exception.', [
                'message' => $exception->getMessage(),
                'serial' => $serial,
            ]);

            return false;
        }
    }

    /**
     * @return array<string, mixed>|null
     */
    public function getControlledDevice(string $serial): ?array
    {
        if (! $this->isConfigured()) {
            return null;
        }

        try {
            $response = $this->apiRequest()->get("{$this->baseUrl}/api/v1/user/devices/{$serial}");

            if ($response->successful()) {
                return $response->json('device');
            }
        } catch (\Throwable $exception) {
            Log::warning('STF controlled device request threw an exception.', [
                'message' => $exception->getMessage(),
                'serial' => $serial,
            ]);
        }

        return null;
    }

    /**
     * @return array<string, mixed>
     */
    public function getFirstDevice(): array
    {
        $devices = $this->getDevices();

        foreach ($devices as $device) {
            if (($device['present'] ?? false) && ($device['ready'] ?? false)) {
                return $device;
            }
        }

        foreach ($devices as $device) {
            if ($device['present'] ?? false) {
                return $device;
            }
        }

        return [];
    }

    /**
     * @param  array<int, array<string, mixed>>|null  $devices
     * @return array<string, mixed>
     */
    public function getDeviceBySerial(string $serial, ?array $devices = null): array
    {
        $devices ??= $this->getDevices();

        foreach ($devices as $device) {
            if (($device['serial'] ?? null) === $serial) {
                return $device;
            }
        }

        return [];
    }

    public function getStreamUrl(string $serial): string
    {
        return "{$this->publicBaseUrl}/#!/c/{$serial}?standalone";
    }

    /**
     * @return array<string, mixed>|null
     */
    private function getCurrentUser(): ?array
    {
        try {
            $response = $this->apiRequest()->get("{$this->baseUrl}/api/v1/user");

            if ($response->successful()) {
                return $response->json('user');
            }
        } catch (\Throwable $exception) {
            Log::warning('STF current user request threw an exception.', [
                'message' => $exception->getMessage(),
            ]);
        }

        return null;
    }

    private function apiRequest(): PendingRequest
    {
        return Http::withToken($this->token)
            ->acceptJson()
            ->timeout(5);
    }

    private function base64UrlEncode(string $value): string
    {
        return Str::of(base64_encode($value))
            ->replace('+', '-')
            ->replace('/', '_')
            ->replace('=', '')
            ->toString();
    }
}
