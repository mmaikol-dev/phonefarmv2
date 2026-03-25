<?php

namespace App\Http\Requests;

use App\Models\User;
use Illuminate\Foundation\Http\FormRequest;
use Illuminate\Validation\Rule;
use Illuminate\Validation\Validator;

class AdminUserUpdateRequest extends FormRequest
{
    public function authorize(): bool
    {
        return $this->user()?->isAdmin() === true;
    }

    /**
     * @return array<string, mixed>
     */
    public function rules(): array
    {
        /** @var User $target */
        $target = $this->route('managedUser');

        return [
            'name' => ['required', 'string', 'max:255'],
            'email' => [
                'required',
                'string',
                'email',
                'max:255',
                Rule::unique('users', 'email')->ignore($target->id),
            ],
            'role' => ['required', Rule::in([User::ROLE_ADMIN, User::ROLE_USER])],
            'assigned_serials' => ['nullable', 'array'],
            'assigned_serials.*' => ['string', 'max:255', 'distinct'],
        ];
    }

    public function withValidator(Validator $validator): void
    {
        $validator->after(function (Validator $validator): void {
            /** @var User $target */
            $target = $this->route('managedUser');
            $actor = $this->user();

            if (! $actor instanceof User || ! $target instanceof User) {
                return;
            }

            if ($target->id === $actor->id && $this->string('role')->toString() !== User::ROLE_ADMIN) {
                $validator->errors()->add('role', 'You cannot remove your own admin access.');
            }
        });
    }
}
