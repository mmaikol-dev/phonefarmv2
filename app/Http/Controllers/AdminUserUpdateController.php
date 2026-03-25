<?php

namespace App\Http\Controllers;

use App\Http\Requests\AdminUserUpdateRequest;
use App\Models\User;
use Illuminate\Http\RedirectResponse;

class AdminUserUpdateController extends Controller
{
    public function __invoke(AdminUserUpdateRequest $request, User $managedUser): RedirectResponse
    {
        $validated = $request->validated();
        $assignedSerials = collect($validated['assigned_serials'] ?? [])
            ->filter(fn (mixed $serial) => is_string($serial) && $serial !== '')
            ->values();

        $managedUser->fill([
            'email' => $validated['email'],
            'name' => $validated['name'],
            'role' => $validated['role'],
        ]);

        if ($managedUser->isDirty('email')) {
            $managedUser->email_verified_at = null;
        }

        $managedUser->save();
        $managedUser->phoneAssignments()->delete();

        if ($assignedSerials->isNotEmpty()) {
            $managedUser->phoneAssignments()->createMany(
                $assignedSerials->map(fn (string $serial) => ['phone_serial' => $serial])->all(),
            );
        }

        return to_route('admin.users');
    }
}
