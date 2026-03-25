<?php

namespace App\Actions\Fortify;

use App\Concerns\PasswordValidationRules;
use App\Concerns\ProfileValidationRules;
use App\Models\User;
use Illuminate\Support\Facades\Validator;
use Laravel\Fortify\Contracts\CreatesNewUsers;

class CreateNewUser implements CreatesNewUsers
{
    use PasswordValidationRules, ProfileValidationRules;

    /**
     * Validate and create a newly registered user.
     *
     * @param  array<string, string>  $input
     */
    public function create(array $input): User
    {
        Validator::make($input, [
            ...$this->profileRules(),
            'password' => $this->passwordRules(),
        ])->validate();

        $email = strtolower($input['email']);
        $configuredAdmins = collect(explode(',', (string) env('ADMIN_EMAILS', '')))
            ->map(fn (string $value) => strtolower(trim($value)))
            ->filter();
        $isFirstUser = User::query()->count() === 0;
        $role = $isFirstUser || $configuredAdmins->contains($email)
            ? User::ROLE_ADMIN
            : User::ROLE_USER;

        return User::create([
            'name' => $input['name'],
            'email' => $input['email'],
            'password' => $input['password'],
            'role' => $role,
        ]);
    }
}
