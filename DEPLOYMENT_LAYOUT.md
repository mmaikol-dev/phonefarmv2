# Deployment Layout

## Short Answer

For the current implementation, Laravel should be hosted on the same machine as:

- STF
- ADB
- the connected phones
- the local `scrcpy` audio tooling

That is the safest and simplest way to keep:

- screen viewing
- touch control
- selected-device audio

working together.

## Why

The current project has two different kinds of functionality:

### 1. STF-based features

These include:

- device listing
- screen view
- touch control
- device selection

These depend on the Laravel app being able to reach the STF API and embed STF pages correctly.

### 2. Local audio-forwarding features

These include:

- starting audio for the selected phone
- stopping the previous phone's audio
- switching audio when a different dashboard phone is selected

These depend on Laravel being able to:

- run local shell scripts
- start `scrcpy`
- use `adb`
- access the phones directly

That means audio is not just an STF API feature. It is a machine-local process feature.

## Recommended Server Layout

Use one main internal server that runs all of these together:

### Same machine

- Laravel app
- STF
- RethinkDB
- ADB
- `scrcpy`
- USB-connected phones

### Flow

1. User opens Laravel dashboard
2. Laravel calls STF and renders the selected phone
3. User selects a phone
4. Laravel switches the local audio process to that phone
5. STF handles screen/touch
6. `scrcpy` handles laptop audio

## Best Current Production Pattern

For this project as it exists now, use:

```text
[One Linux server]
  ├── Laravel app
  ├── STF server
  ├── RethinkDB
  ├── ADB
  ├── scrcpy
  └── USB-connected phones
```

This keeps everything in the same runtime environment and avoids cross-machine control issues.

## If Laravel Is Hosted Somewhere Else

If Laravel is hosted on another machine, the current audio implementation will not reliably work unless you add another service layer.

That is because the remote Laravel server would not automatically have:

- access to the USB-connected phones
- ADB device visibility
- local `scrcpy` execution
- permission to manage the local audio process

In that case, you would need a separate audio worker or device-control worker running near STF and the phones.

## Future Scalable Architecture

If you later want to separate responsibilities, the cleaner architecture would be:

```text
[Web App Server]
  └── Laravel

[Device Server]
  ├── STF
  ├── RethinkDB
  ├── ADB
  ├── scrcpy
  └── USB-connected phones
```

Then Laravel would talk to a local device-control service on the device server.

That service would be responsible for:

- starting/stopping audio
- tracking active phone audio sessions
- exposing safe API endpoints back to Laravel

But that is a later architecture, not the current one.

## Recommended Decision Right Now

For now, host Laravel on the same machine as STF if you want the current selected-device audio feature to work as designed.

That gives you:

- simplest deployment
- fewer moving parts
- reliable ADB access
- reliable local audio switching
- easier debugging

## Checklist

If you deploy this current version on the same machine, make sure the server has:

- PHP/Laravel runtime
- Node/Vite build output
- STF installed and reachable
- RethinkDB running
- ADB working
- `scrcpy 3.3.4` available in:
  - `/home/atlas/PHONE FARM/tools/scrcpy-v3.3.4`
- USB-connected phones visible in `adb devices`
- correct `.env` values for STF URLs and token

## Summary

Yes, for this implementation, the correct deployment choice is:

- host Laravel on the same machine as STF and the phones

That is especially important if you want:

- audio to follow the selected device
- Laravel to manage audio switching directly
