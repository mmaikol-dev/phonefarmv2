<?php

namespace Tests\Feature;

use App\Models\User;
use App\Services\PhoneAudioService;
use App\Services\STFService;
use Inertia\Testing\AssertableInertia as Assert;
use Mockery\MockInterface;
use Tests\TestCase;

class DashboardTest extends TestCase
{
    public function test_guests_are_redirected_to_the_login_page()
    {
        $response = $this->get(route('dashboard', ['serial' => 'device-123']));
        $response->assertRedirect(route('login'));
    }

    public function test_admin_users_see_the_device_picker_before_selecting_a_phone()
    {
        $this->mock(PhoneAudioService::class, function (MockInterface $mock): void {
            $mock->shouldReceive('getStatus')->once()->andReturn([
                'active' => false,
                'message' => 'Audio is idle.',
                'pid' => null,
                'serial' => null,
                'source' => 'output',
            ]);
        });

        $this->mock(STFService::class, function (MockInterface $mock): void {
            $mock->shouldReceive('getConfigurationError')->once()->andReturnNull();
            $mock->shouldReceive('getBrowserSessionBootstrapUrl')->once()->andReturn('http://localhost:7100/?jwt=test-token');
            $mock->shouldReceive('getControlSocketUrl')->once()->andReturn('http://localhost:7110/');
            $devices = [[
                'channel' => 'device-channel-123',
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
                'using' => true,
            ]];
            $mock->shouldReceive('getDevices')->once()->andReturn($devices);
            $mock->shouldReceive('getBaseUrl')->once()->andReturn('http://localhost:7100');
        });

        $user = User::factory()->admin()->make();
        $this->actingAs($user);

        $response = $this->get(route('dashboard'));

        $response
            ->assertOk()
            ->assertInertia(fn (Assert $page) => $page
                ->component('dashboard')
                ->where('audioStatus.serial', null)
                ->where('canOpenStf', true)
                ->where('controlSocketUrl', 'http://localhost:7110/')
                ->where('device', null)
                ->where('devices.0.serial', 'device-123')
                ->where('error', null)
                ->where('selectedSerial', null)
                ->where('stfBaseUrl', 'http://localhost:7100')
                ->where('stfSessionUrl', 'http://localhost:7100/?jwt=test-token')
                ->where('streamUrl', null),
            );
    }

    public function test_authenticated_users_see_a_helpful_error_when_stf_is_not_configured()
    {
        $this->mock(PhoneAudioService::class, function (MockInterface $mock): void {
            $mock->shouldReceive('getStatus')->once()->andReturn([
                'active' => false,
                'message' => 'Audio is idle.',
                'pid' => null,
                'serial' => null,
                'source' => 'output',
            ]);
        });

        $this->mock(STFService::class, function (MockInterface $mock): void {
            $mock->shouldReceive('getConfigurationError')->once()->andReturn(
                'Set STF_TOKEN in your .env file so Laravel can talk to the STF API.',
            );
            $mock->shouldReceive('getBrowserSessionBootstrapUrl')->once()->andReturnNull();
            $mock->shouldReceive('getControlSocketUrl')->once()->andReturn('http://localhost:7110/');
            $mock->shouldReceive('getBaseUrl')->once()->andReturn('http://localhost:7100');
        });

        $user = User::factory()->admin()->make();
        $this->actingAs($user);

        $response = $this->get(route('dashboard'));

        $response
            ->assertOk()
            ->assertInertia(fn (Assert $page) => $page
                ->component('dashboard')
                ->where('audioStatus.active', false)
                ->where('canOpenStf', true)
                ->where('controlSocketUrl', 'http://localhost:7110/')
                ->where('device', null)
                ->where('devices', [])
                ->where('error', 'Set STF_TOKEN in your .env file so Laravel can talk to the STF API.')
                ->where('selectedSerial', null)
                ->where('stfBaseUrl', 'http://localhost:7100')
                ->where('stfSessionUrl', null)
                ->where('streamUrl', null),
            );
    }

    public function test_authenticated_users_claim_an_available_device_before_rendering_the_dashboard()
    {
        $this->mock(PhoneAudioService::class, function (MockInterface $mock): void {
            $mock->shouldReceive('getStatus')->once()->andReturn([
                'active' => false,
                'message' => 'Audio is idle.',
                'pid' => null,
                'serial' => null,
                'source' => 'output',
            ]);
            $mock->shouldReceive('syncToDevice')->once()->with('device-123')->andReturn([
                'active' => true,
                'message' => 'Audio is following the selected phone.',
                'pid' => 2222,
                'serial' => 'device-123',
                'source' => 'output',
            ]);
        });

        $this->mock(STFService::class, function (MockInterface $mock): void {
            $mock->shouldReceive('getConfigurationError')->once()->andReturnNull();
            $mock->shouldReceive('getBrowserSessionBootstrapUrl')->once()->andReturn('http://localhost:7100/?jwt=test-token');
            $mock->shouldReceive('getControlSocketUrl')->once()->andReturn('http://localhost:7110/');
            $devices = [[
                'serial' => 'device-123',
                'present' => true,
                'ready' => true,
                'using' => false,
            ]];
            $mock->shouldReceive('getDevices')->once()->andReturn($devices);
            $mock->shouldReceive('getDeviceBySerial')->once()->with('device-123', $devices)->andReturn($devices[0]);
            $mock->shouldReceive('claimDevice')->once()->with('device-123')->andReturnTrue();
            $mock->shouldReceive('getControlledDevice')->once()->with('device-123')->andReturn([
                'channel' => 'device-channel-123',
                'display' => [
                    'height' => 2400,
                    'url' => 'ws://127.0.0.1:7400',
                    'width' => 1080,
                ],
                'serial' => 'device-123',
                'using' => true,
            ]);
            $mock->shouldReceive('getStreamUrl')->once()->with('device-123')->andReturn('http://localhost:7100/#!/c/device-123?standalone');
            $mock->shouldReceive('getBaseUrl')->once()->andReturn('http://localhost:7100');
        });

        $user = User::factory()->admin()->make();
        $this->actingAs($user);

        $response = $this->get(route('dashboard', ['serial' => 'device-123']));

        $response
            ->assertOk()
            ->assertInertia(fn (Assert $page) => $page
                ->component('dashboard')
                ->where('canOpenStf', true)
                ->where('device.channel', 'device-channel-123')
                ->where('device.using', true)
                ->where('selectedSerial', 'device-123')
                ->where('stfSessionUrl', 'http://localhost:7100/?jwt=test-token')
                ->where('streamUrl', 'http://localhost:7100/#!/c/device-123?standalone'),
            );
    }

    public function test_authenticated_users_can_select_a_specific_device_from_the_query_string()
    {
        $this->mock(PhoneAudioService::class, function (MockInterface $mock): void {
            $mock->shouldReceive('getStatus')->once()->andReturn([
                'active' => false,
                'message' => 'Audio is idle.',
                'pid' => null,
                'serial' => null,
                'source' => 'output',
            ]);
            $mock->shouldReceive('syncToDevice')->once()->with('device-222')->andReturn([
                'active' => true,
                'message' => 'Audio is following the selected phone.',
                'pid' => 3333,
                'serial' => 'device-222',
                'source' => 'output',
            ]);
        });

        $this->mock(STFService::class, function (MockInterface $mock): void {
            $mock->shouldReceive('getConfigurationError')->once()->andReturnNull();
            $mock->shouldReceive('getBrowserSessionBootstrapUrl')->once()->andReturn('http://localhost:7100/?jwt=test-token');
            $mock->shouldReceive('getControlSocketUrl')->once()->andReturn('http://localhost:7110/');
            $devices = [
                [
                    'serial' => 'device-111',
                    'present' => true,
                    'ready' => true,
                    'using' => true,
                ],
                [
                    'channel' => 'device-channel-222',
                    'serial' => 'device-222',
                    'display' => [
                        'height' => 2400,
                        'url' => 'ws://127.0.0.1:7402',
                        'width' => 1080,
                    ],
                    'present' => true,
                    'ready' => true,
                    'using' => true,
                ],
            ];
            $mock->shouldReceive('getDevices')->once()->andReturn($devices);
            $mock->shouldReceive('getDeviceBySerial')->once()->with('device-222', $devices)->andReturn($devices[1]);
            $mock->shouldReceive('getStreamUrl')->once()->with('device-222')->andReturn('http://localhost:7100/#!/c/device-222?standalone');
            $mock->shouldReceive('getBaseUrl')->once()->andReturn('http://localhost:7100');
        });

        $user = User::factory()->admin()->make();
        $this->actingAs($user);

        $response = $this->get(route('dashboard', ['serial' => 'device-222']));

        $response
            ->assertOk()
            ->assertInertia(fn (Assert $page) => $page
                ->component('dashboard')
                ->where('audioStatus.serial', 'device-222')
                ->where('canOpenStf', true)
                ->where('device.serial', 'device-222')
                ->where('selectedSerial', 'device-222')
                ->where('streamUrl', 'http://localhost:7100/#!/c/device-222?standalone'),
            );
    }
}
