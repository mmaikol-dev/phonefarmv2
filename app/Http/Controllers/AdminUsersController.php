<?php

namespace App\Http\Controllers;

use App\Models\User;
use App\Services\STFService;
use Inertia\Inertia;
use Inertia\Response;

class AdminUsersController extends Controller
{
    public function __construct(
        private readonly STFService $stf,
    ) {}

    public function __invoke(): Response
    {
        $users = User::query()
            ->with('phoneAssignments:user_id,phone_serial')
            ->latest()
            ->get([
                'id',
                'name',
                'email',
                'role',
                'email_verified_at',
                'created_at',
            ])
            ->map(fn (User $user) => [
                'assigned_serials' => $user->phoneAssignments->pluck('phone_serial')->values()->all(),
                'created_at' => $user->created_at,
                'email' => $user->email,
                'email_verified_at' => $user->email_verified_at,
                'id' => $user->id,
                'name' => $user->name,
                'role' => $user->role,
            ]);

        $availablePhones = [];

        if ($this->stf->getConfigurationError() === null) {
            $availablePhones = collect($this->stf->getDevices())
                ->map(fn (array $device) => [
                    'label' => trim(implode(' ', array_filter([
                        $device['manufacturer'] ?? null,
                        $device['model'] ?? null,
                    ]))) ?: ((string) ($device['serial'] ?? 'Unknown device')),
                    'present' => (bool) ($device['present'] ?? false),
                    'ready' => (bool) ($device['ready'] ?? false),
                    'serial' => (string) ($device['serial'] ?? ''),
                ])
                ->filter(fn (array $device) => $device['serial'] !== '')
                ->keyBy('serial');
        }

        $assignedPhoneOptions = $users
            ->flatMap(fn (array $user) => $user['assigned_serials'])
            ->unique()
            ->mapWithKeys(fn (string $serial) => [$serial => [
                'label' => $serial,
                'present' => false,
                'ready' => false,
                'serial' => $serial,
            ]]);

        return Inertia::render('admin/users', [
            'availablePhones' => $availablePhones
                ? $availablePhones->union($assignedPhoneOptions)->values()->all()
                : $assignedPhoneOptions->values()->all(),
            'users' => $users,
        ]);
    }
}
