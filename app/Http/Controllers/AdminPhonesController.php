<?php

namespace App\Http\Controllers;

use App\Services\STFService;
use Inertia\Inertia;
use Inertia\Response;

class AdminPhonesController extends Controller
{
    public function __construct(private readonly STFService $stf) {}

    public function __invoke(): Response
    {
        $error = $this->stf->getConfigurationError();
        $devices = [];
        $stfSessionUrl = null;

        if ($error === null) {
            $devices = collect($this->stf->getDevices())
                ->map(function (array $device): array {
                    $device['streamUrl'] = $this->stf->getStreamUrl((string) $device['serial']);

                    return $device;
                })
                ->all();
            $stfSessionUrl = $this->stf->getBrowserSessionBootstrapUrl();

            if ($devices === []) {
                $error = 'No phones are currently available in STF.';
            }
        }

        return Inertia::render('admin/phones', [
            'devices' => $devices,
            'error' => $error,
            'stfSessionUrl' => $stfSessionUrl,
        ]);
    }
}
