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
        $this->baseUrl = rtrim((string) config('services.stf.base_url', ''), '/');
        $this->token = (string) config('services.stf.token', '');
    }

    public function getBaseUrl(): string
    {
        return $this->baseUrl;
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
            $response = Http::withToken($this->token)
                ->acceptJson()
                ->timeout(5)
                ->get("{$this->baseUrl}/api/v1/devices");

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

    public function getStreamUrl(string $serial): string
    {
        return "{$this->baseUrl}/#!/control/{$serial}";
    }
}
