<?php

namespace Tests\Feature;

use App\Models\User;
use App\Services\STFService;
use Inertia\Testing\AssertableInertia as Assert;
use Mockery\MockInterface;
use Tests\TestCase;

class DashboardTest extends TestCase
{
    public function test_guests_are_redirected_to_the_login_page()
    {
        $response = $this->get(route('dashboard'));
        $response->assertRedirect(route('login'));
    }

    public function test_authenticated_users_can_visit_the_dashboard_with_a_connected_device()
    {
        $this->mock(STFService::class, function (MockInterface $mock): void {
            $mock->shouldReceive('getConfigurationError')->once()->andReturnNull();
            $mock->shouldReceive('getFirstDevice')->once()->andReturn([
                'serial' => 'device-123',
                'display' => [
                    'height' => 2400,
                    'url' => 'ws://127.0.0.1:7400',
                    'width' => 1080,
                ],
                'manufacturer' => 'Xiaomi',
                'model' => 'Redmi Note 10 Pro',
                'platform' => 'Android',
                'version' => '14',
                'present' => true,
                'ready' => true,
            ]);
            $mock->shouldReceive('getStreamUrl')->once()->with('device-123')->andReturn('http://localhost:7100/#!/control/device-123');
            $mock->shouldReceive('getBaseUrl')->once()->andReturn('http://localhost:7100');
        });

        $user = User::factory()->make();
        $this->actingAs($user);

        $response = $this->get(route('dashboard'));

        $response
            ->assertOk()
            ->assertInertia(fn (Assert $page) => $page
                ->component('dashboard')
                ->where('device.serial', 'device-123')
                ->where('device.display.url', 'ws://127.0.0.1:7400')
                ->where('error', null)
                ->where('stfBaseUrl', 'http://localhost:7100')
                ->where('streamUrl', 'http://localhost:7100/#!/control/device-123'),
            );
    }

    public function test_authenticated_users_see_a_helpful_error_when_stf_is_not_configured()
    {
        $this->mock(STFService::class, function (MockInterface $mock): void {
            $mock->shouldReceive('getConfigurationError')->once()->andReturn(
                'Set STF_TOKEN in your .env file so Laravel can talk to the STF API.',
            );
            $mock->shouldReceive('getBaseUrl')->once()->andReturn('http://localhost:7100');
        });

        $user = User::factory()->make();
        $this->actingAs($user);

        $response = $this->get(route('dashboard'));

        $response
            ->assertOk()
            ->assertInertia(fn (Assert $page) => $page
                ->component('dashboard')
                ->where('device', null)
                ->where('error', 'Set STF_TOKEN in your .env file so Laravel can talk to the STF API.')
                ->where('stfBaseUrl', 'http://localhost:7100')
                ->where('streamUrl', null),
            );
    }
}
