<?php

namespace App\Http\Controllers;

use App\Services\PhoneAudioService;
use App\Services\STFService;
use Illuminate\Http\Request;
use Inertia\Inertia;
use Inertia\Response;

class DashboardController extends Controller
{
    public function __construct(
        private readonly PhoneAudioService $audio,
        private readonly STFService $stf,
    ) {}

    public function __invoke(Request $request): Response
    {
        $actor = $request->user();
        $devices = [];
        $device = null;
        $selectedSerial = $request->string('serial')->toString();
        $streamUrl = null;
        $audioStatus = $this->audio->getStatus();
        $error = $this->stf->getConfigurationError();

        if ($error === null) {
            $devices = $this->stf->getDevices();

            if ($actor !== null && ! $actor->isAdmin()) {
                $allowedSerials = $actor->phoneAssignments()->pluck('phone_serial');

                $devices = collect($devices)
                    ->filter(fn (array $device) => $allowedSerials->contains((string) ($device['serial'] ?? '')))
                    ->values()
                    ->all();
            }

            if ($selectedSerial !== '') {
                $device = $this->stf->getDeviceBySerial($selectedSerial, $devices);
            } elseif ($devices === []) {
                $error = $request->user()?->isAdmin()
                    ? 'No phone is currently available in STF. Start STF, connect a device, and refresh the dashboard.'
                    : 'No phones are assigned to your account right now. Ask an admin to grant phone access.';
            }

            if ($device !== null && $device !== []) {
                if (($device['using'] ?? false) !== true) {
                    $this->stf->claimDevice((string) $device['serial']);

                    $controlledDevice = $this->stf->getControlledDevice((string) $device['serial']);

                    if ($controlledDevice !== null) {
                        $device = $controlledDevice;
                    }
                }

                $streamUrl = $this->stf->getStreamUrl((string) $device['serial']);
                $audioStatus = $this->audio->syncToDevice((string) $device['serial']);
            } elseif ($selectedSerial !== '' && $devices !== []) {
                $error = 'That phone is no longer available in STF. Pick another device from the list.';
            }
        }

        return Inertia::render('dashboard', [
            'audioStatus' => $audioStatus,
            'canOpenStf' => $actor?->isAdmin() === true,
            'controlSocketUrl' => $this->stf->getControlSocketUrl(),
            'device' => $device,
            'devices' => $devices,
            'error' => $error,
            'selectedSerial' => $device['serial'] ?? ($selectedSerial !== '' ? $selectedSerial : null),
            'stfBaseUrl' => $this->stf->getBaseUrl(),
            'stfSessionUrl' => $this->stf->getBrowserSessionBootstrapUrl(),
            'streamUrl' => $streamUrl,
        ]);
    }
}
