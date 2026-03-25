<?php

namespace App\Http\Controllers;

use Inertia\Inertia;
use Inertia\Response;

class AdminController extends Controller
{
    public function __invoke(): Response
    {
        return Inertia::render('admin/index', [
            'links' => [
                [
                    'description' => 'View everyone who can sign in to the platform.',
                    'href' => '/admin/users',
                    'title' => 'Users',
                ],
                [
                    'description' => 'See every phone currently reported by STF.',
                    'href' => '/admin/phones',
                    'title' => 'Phones',
                ],
            ],
        ]);
    }
}
