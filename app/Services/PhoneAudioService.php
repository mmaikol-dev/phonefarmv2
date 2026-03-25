<?php

namespace App\Services;

use Symfony\Component\Process\Process;

class PhoneAudioService
{
    /**
     * @return array<string, bool|int|string|null>
     */
    public function syncToDevice(string $serial): array
    {
        $current = $this->getStatus();

        if (($current['active'] ?? false) === true && ($current['serial'] ?? null) === $serial) {
            return $current;
        }

        $this->stop();

        return $this->start($serial);
    }

    /**
     * @return array<string, bool|int|string|null>
     */
    public function getStatus(): array
    {
        $session = $this->readSession();

        if ($session === null) {
            return $this->emptyStatus();
        }

        $pid = (int) ($session['pid'] ?? 0);

        if ($pid < 1 || ! $this->isRunning($pid)) {
            $this->clearSession();

            return $this->emptyStatus();
        }

        return [
            'active' => true,
            'message' => 'Audio is following the selected phone.',
            'pid' => $pid,
            'serial' => (string) ($session['serial'] ?? ''),
            'source' => (string) ($session['source'] ?? 'output'),
        ];
    }

    /**
     * @return array<string, bool|int|string|null>
     */
    public function stop(): array
    {
        $session = $this->readSession();

        if ($session === null) {
            return $this->emptyStatus();
        }

        $pid = (int) ($session['pid'] ?? 0);

        if ($pid > 0) {
            Process::fromShellCommandline('kill '.intval($pid))->run();
        }

        $this->clearSession();

        return $this->emptyStatus();
    }

    /**
     * @return array<string, bool|int|string|null>
     */
    private function start(string $serial): array
    {
        $logPath = storage_path('logs/phone-audio.log');
        $command = sprintf(
            'cd %s && ANDROID_SERIAL=%s SCRCPY_AUDIO_SOURCE=%s nohup %s > %s 2>&1 < /dev/null & echo $!',
            escapeshellarg(base_path()),
            escapeshellarg($serial),
            escapeshellarg((string) config('services.stf.audio_source', 'output')),
            escapeshellarg(base_path('scripts/start-phone-audio.sh')),
            escapeshellarg($logPath),
        );

        $process = Process::fromShellCommandline($command);
        $process->run();

        $pid = (int) trim($process->getOutput());

        if (! $process->isSuccessful() || $pid < 1) {
            return [
                'active' => false,
                'message' => 'Audio could not be started for the selected phone.',
                'pid' => null,
                'serial' => $serial,
                'source' => (string) config('services.stf.audio_source', 'output'),
            ];
        }

        usleep(750000);

        if (! $this->isRunning($pid)) {
            return [
                'active' => false,
                'message' => $this->readLastLogLine($logPath) ?? 'Audio could not be started for the selected phone.',
                'pid' => null,
                'serial' => $serial,
                'source' => (string) config('services.stf.audio_source', 'output'),
            ];
        }

        $session = [
            'pid' => $pid,
            'serial' => $serial,
            'source' => (string) config('services.stf.audio_source', 'output'),
        ];

        file_put_contents($this->sessionPath(), json_encode($session, JSON_PRETTY_PRINT | JSON_THROW_ON_ERROR));

        return [
            'active' => true,
            'message' => 'Audio is following the selected phone.',
            'pid' => $pid,
            'serial' => $serial,
            'source' => (string) config('services.stf.audio_source', 'output'),
        ];
    }

    private function sessionPath(): string
    {
        return storage_path('app/phone-audio-session.json');
    }

    /**
     * @return array<string, mixed>|null
     */
    private function readSession(): ?array
    {
        $path = $this->sessionPath();

        if (! is_file($path)) {
            return null;
        }

        $contents = file_get_contents($path);

        if ($contents === false || $contents === '') {
            return null;
        }

        /** @var array<string, mixed>|null $decoded */
        $decoded = json_decode($contents, true);

        return is_array($decoded) ? $decoded : null;
    }

    private function clearSession(): void
    {
        $path = $this->sessionPath();

        if (is_file($path)) {
            @unlink($path);
        }
    }

    private function isRunning(int $pid): bool
    {
        $process = Process::fromShellCommandline('kill -0 '.intval($pid));
        $process->run();

        return $process->isSuccessful();
    }

    /**
     * @return array<string, bool|int|string|null>
     */
    private function emptyStatus(): array
    {
        return [
            'active' => false,
            'message' => 'Audio is idle.',
            'pid' => null,
            'serial' => null,
            'source' => (string) config('services.stf.audio_source', 'output'),
        ];
    }

    private function readLastLogLine(string $path): ?string
    {
        if (! is_file($path)) {
            return null;
        }

        $lines = file($path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);

        if (! is_array($lines) || $lines === []) {
            return null;
        }

        return trim((string) end($lines));
    }
}
