# Phone Audio Setup

## Goal

The goal was to make phone audio play through the laptop while keeping:

- STF for screen and touch control
- Laravel as the dashboard shell

The desired result was:

- see the phone in the dashboard
- control the phone from the dashboard
- hear the phone's audio on the laptop speakers or headset

## Problem

STF handles screen streaming and touch control well, but it does not provide a simple built-in laptop audio forwarding path in the same way.

So even after the dashboard was working, audio was still playing from the physical phone instead of the laptop.

## Decision

Instead of trying to force audio through STF, we used a parallel audio-forwarding tool.

The chosen short-term approach was:

- keep STF for screen and touch
- use `scrcpy` separately for phone audio on the laptop

This was the fastest practical path without building a full SIP or VoIP stack.

## What We Checked First

We checked what was already available on the machine.

### Installed tools

- `adb` was already installed
- `scrcpy` was not installed
- `ffmpeg` was not installed

### Project state

The Laravel project had no existing audio pipeline.

That confirmed audio needed to be added as a separate system rather than as a small STF config change.

## Important Finding

Ubuntu's packaged `scrcpy` version available on this machine was too old:

```text
1.25
```

That version was not a good fit for modern built-in audio forwarding.

So instead of using the Ubuntu package, we downloaded a newer local release of `scrcpy`.

## What We Did

### 1. Downloaded a newer `scrcpy` build locally

We downloaded and extracted:

```text
scrcpy 3.3.4
```

into:

```text
/home/atlas/PHONE FARM/tools/scrcpy-v3.3.4
```

This gave us:

- a current `scrcpy` binary
- a bundled `adb` binary
- the matching `scrcpy-server`

### 2. Verified the `scrcpy` binary works

We checked the version and confirmed the local build runs correctly.

### 3. Verified the phone is visible to ADB

The connected phone detected on this machine was:

```text
aece3bbd
```

### 4. Chose host `adb` instead of bundled `adb`

Inside the sandbox, the bundled `adb` could not start its own daemon reliably.

The system `adb` was already working with the phone, so we pointed `scrcpy` at:

```text
/usr/bin/adb
```

instead of its bundled copy.

### 5. Created a reusable launcher script

We added:

- [start-phone-audio.sh](/home/atlas/PHONE%20FARM/phonefarmv2/scripts/start-phone-audio.sh)

This script:

- uses the local `scrcpy 3.3.4`
- uses the host `adb`
- defaults to the connected device serial
- launches audio-only forwarding

## Launcher Behavior

The launcher script uses these defaults:

- device serial: `aece3bbd`
- audio source: `output`
- no video window
- audio required

It runs `scrcpy` in audio-only mode with:

```bash
--no-video
--no-window
--require-audio
--audio-source=output
```

## Commands Used

### Check available Ubuntu package versions

```bash
apt-cache policy scrcpy ffmpeg
```

### Check ADB

```bash
adb version
adb devices
```

### Download the local `scrcpy` release

```bash
curl -L https://sourceforge.net/projects/scrcpy.mirror/files/v3.3.4/scrcpy-linux-x86_64-v3.3.4.tar.gz/download \
  -o /home/atlas/PHONE\ FARM/tools-scrcpy-v3.3.4.tar.gz
```

### Extract it

```bash
mkdir -p /home/atlas/PHONE\ FARM/tools/scrcpy-v3.3.4
tar -xzf /home/atlas/PHONE\ FARM/tools-scrcpy-v3.3.4.tar.gz \
  -C /home/atlas/PHONE\ FARM/tools/scrcpy-v3.3.4 \
  --strip-components=1
```

### Verify the binary

```bash
'/home/atlas/PHONE FARM/tools/scrcpy-v3.3.4/scrcpy' --version
```

### Start phone audio

```bash
cd /home/atlas/PHONE\ FARM/phonefarmv2
./scripts/start-phone-audio.sh
```

## How To Use It

### Default audio mode

From the project directory:

```bash
cd /home/atlas/PHONE\ FARM/phonefarmv2
./scripts/start-phone-audio.sh
```

This starts audio-only forwarding from the phone to the laptop.

### Try another audio source

By default, the launcher uses:

```text
output
```

You can override it like this:

```bash
SCRCPY_AUDIO_SOURCE=playback ./scripts/start-phone-audio.sh
```

Useful possible sources include:

- `output`
- `playback`
- `voice-call`
- `voice-call-uplink`
- `voice-call-downlink`
- `mic`

Example:

```bash
SCRCPY_AUDIO_SOURCE=voice-call ./scripts/start-phone-audio.sh
```

## Notes About Audio Sources

- `output` is a good default for general phone audio
- `playback` may work better for app audio on some phones
- `voice-call` is the first thing to try if the goal is call audio
- some Android devices restrict or block certain call-audio capture modes

So if one source gives no sound, try another.

## Requirements

For this to work:

- USB debugging must remain enabled
- the phone must remain connected over ADB
- the laptop must already be authorized on the phone

Check connected devices with:

```bash
adb devices
```

## Current Limitation

This audio path is separate from the Laravel dashboard.

That means:

- Laravel dashboard handles UI and phone control
- STF handles screen and touch
- `scrcpy` handles laptop audio

So this is currently a parallel audio solution, not embedded browser audio inside the dashboard itself.

## Summary

We did not add audio through STF directly.

Instead, we:

1. confirmed STF was not the right layer for laptop audio
2. chose `scrcpy` as the short-term audio-forwarding tool
3. avoided the outdated Ubuntu package
4. downloaded a current local `scrcpy` release
5. reused the working host `adb`
6. added a launcher script to make audio forwarding easy to start again
