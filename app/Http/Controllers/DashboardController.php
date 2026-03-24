<?php

namespace App\Http\Controllers;

use App\Services\STFService;
use Inertia\Inertia;
use Inertia\Response;

class DashboardController extends Controller
{
    public function __construct(private readonly STFService $stf) {}

    public function __invoke(): Response
    {
        $device = null;
        $streamUrl = null;
        $error = $this->stf->getConfigurationError();

        if ($error === null) {
            $device = $this->stf->getFirstDevice();

            if ($device === []) {
                $device = null;
                $error = 'No phone is currently available in STF. Start STF, connect a device, and refresh the dashboard.';
            } else {
                $streamUrl = $this->stf->getStreamUrl((string) $device['serial']);
            }
        }

        return Inertia::render('dashboard', [
            'device' => $device,
            'error' => $error,
            'stfBaseUrl' => $this->stf->getBaseUrl(),
            'streamUrl' => $streamUrl,
        ]);
    }
}
