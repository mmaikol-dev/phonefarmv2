<?php

namespace Tests\Feature;

use App\Models\User;
use App\Services\STFService;
use Inertia\Testing\AssertableInertia as Assert;
use Mockery\MockInterface;
use Tests\TestCase;

class AdminAccessTest extends TestCase
{
    public function test_admin_users_can_open_the_admin_page(): void
    {
        $user = User::factory()->admin()->make();

        $response = $this->actingAs($user)->get('/admin');

        $response->assertOk();
    }

    public function test_normal_users_cannot_open_the_admin_page(): void
    {
        $user = User::factory()->make();

        $response = $this->actingAs($user)->get('/admin');

        $response->assertForbidden();
    }

    public function test_admin_users_can_open_the_admin_phones_wall(): void
    {
        $this->mock(STFService::class, function (MockInterface $mock): void {
            $mock->shouldReceive('getConfigurationError')->once()->andReturnNull();
            $mock->shouldReceive('getDevices')->once()->andReturn([
                [
                    'serial' => 'device-123',
                    'name' => 'Redmi Note 10 Pro',
                    'present' => true,
                    'ready' => true,
                ],
            ]);
            $mock->shouldReceive('getStreamUrl')->once()->with('device-123')->andReturn('http://localhost:7100/#!/c/device-123?standalone');
            $mock->shouldReceive('getBrowserSessionBootstrapUrl')->once()->andReturn('http://localhost:7100/?jwt=test-token');
        });

        $user = User::factory()->admin()->make();

        $response = $this->actingAs($user)->get('/admin/phones');

        $response
            ->assertOk()
            ->assertInertia(fn (Assert $page) => $page
                ->component('admin/phones')
                ->where('devices.0.serial', 'device-123')
                ->where('devices.0.streamUrl', 'http://localhost:7100/#!/c/device-123?standalone')
                ->where('stfSessionUrl', 'http://localhost:7100/?jwt=test-token'),
            );
    }
}
