<?php

use App\Http\Controllers\AdminController;
use App\Http\Controllers\AdminPhonesController;
use App\Http\Controllers\AdminUsersController;
use App\Http\Controllers\AdminUserUpdateController;
use App\Http\Controllers\DashboardController;
use Illuminate\Support\Facades\Route;
use Laravel\Fortify\Features;

Route::inertia('/', 'welcome', [
    'canRegister' => Features::enabled(Features::registration()),
])->name('home');

Route::middleware(['auth', 'verified'])->group(function () {
    Route::get('dashboard', DashboardController::class)->name('dashboard');
    Route::middleware('admin')->group(function () {
        Route::get('admin', AdminController::class)->name('admin.index');
        Route::get('admin/users', AdminUsersController::class)->name('admin.users');
        Route::patch('admin/users/{managedUser}', AdminUserUpdateController::class)->name('admin.users.update');
        Route::get('admin/phones', AdminPhonesController::class)->name('admin.phones');
    });
});

require __DIR__.'/settings.php';
