import { Head, Link } from '@inertiajs/react';
import {
    ExternalLink,
    RefreshCcw,
    TriangleAlert,
    Wifi,
} from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from '@/components/ui/card';
import AppLayout from '@/layouts/app-layout';
import { dashboard } from '@/routes';
import type { BreadcrumbItem } from '@/types';

type Device = {
    channel?: string;
    display?: {
        height: number;
        url: string;
        width: number;
    };
    serial: string;
    manufacturer?: string;
    model?: string;
    name?: string;
    platform?: string;
    version?: string;
    sdk?: string | number;
    present?: boolean;
    ready?: boolean;
    using?: boolean;
};

type Props = {
    audioStatus: {
        active: boolean;
        message: string | null;
        pid: number | null;
        serial: string | null;
        source: string | null;
    };
    canOpenStf: boolean;
    device: Device | null;
    devices: Device[];
    error: string | null;
    selectedSerial: string | null;
    stfBaseUrl: string;
    stfSessionUrl: string | null;
    streamUrl: string | null;
};

const breadcrumbs: BreadcrumbItem[] = [
    {
        title: 'Live phone',
        href: dashboard(),
    },
];

export default function Dashboard({
    audioStatus,
    canOpenStf,
    device,
    devices,
    error,
    selectedSerial,
    stfBaseUrl,
    stfSessionUrl,
    streamUrl,
}: Props) {
    const fallbackDeviceName = [device?.manufacturer, device?.model]
        .filter(Boolean)
        .join(' ');
    const deviceName = device?.name || fallbackDeviceName || device?.model || 'Unknown device';

    const infoRows = canOpenStf
        ? [
              { label: 'Serial', value: device?.serial ?? 'Unavailable' },
              { label: 'Device', value: device?.name ?? device?.model ?? 'Unknown' },
              { label: 'Manufacturer', value: device?.manufacturer ?? 'Unknown' },
              { label: 'Platform', value: device?.platform ?? 'Android' },
              { label: 'Version', value: device?.version ?? 'Unknown' },
              { label: 'SDK', value: device?.sdk ? String(device.sdk) : 'Unknown' },
          ]
        : [{ label: 'Device name', value: deviceName }];

    return (
        <AppLayout breadcrumbs={breadcrumbs}>
            <Head title="Live Phone" />

            <div className="flex h-full flex-1 flex-col gap-6 overflow-x-auto rounded-xl p-4">
                <div className="flex flex-col gap-4 rounded-3xl border border-sidebar-border/70 bg-linear-to-br from-background via-background to-muted/30 p-6 shadow-sm dark:border-sidebar-border md:flex-row md:items-start md:justify-between">
                    <div className="space-y-3">
                        <Badge variant="outline" className="gap-1.5">
                            <Wifi className="size-3.5" />
                            STF remote control
                        </Badge>
                        <Badge variant={audioStatus.active ? 'default' : 'outline'} className="gap-1.5">
                            <Wifi className="size-3.5" />
                            {audioStatus.active
                                ? `Audio: ${audioStatus.serial ?? 'active'}`
                                : 'Audio idle'}
                        </Badge>
                        <div className="space-y-2">
                            <h1 className="text-3xl font-semibold tracking-tight">
                                Live phone dashboard
                            </h1>
                            <p className="max-w-2xl text-sm text-muted-foreground">
                                View your connected Android device inside the app shell and jump
                                straight into STF when you need the full control panel.
                            </p>
                        </div>
                    </div>

                    <div className="flex flex-wrap gap-3">
                        <Button variant="outline" asChild>
                            <Link href={dashboard()}>
                                <RefreshCcw />
                                Refresh device
                            </Link>
                        </Button>

                        {canOpenStf && stfBaseUrl ? (
                            <Button asChild>
                                <a
                                    href={stfBaseUrl}
                                    target="_blank"
                                    rel="noreferrer"
                                >
                                    <ExternalLink />
                                    Open STF
                                </a>
                            </Button>
                        ) : null}
                    </div>
                </div>

                <div className="grid gap-6 xl:grid-cols-[minmax(0,1.1fr)_minmax(360px,0.9fr)]">
                    <Card className="overflow-hidden rounded-[2rem] border-sidebar-border/70 pt-0 dark:border-sidebar-border">
                        <CardHeader className="border-b bg-muted/40 px-6 py-5">
                            <CardTitle>Phone screen</CardTitle>
                            <CardDescription>
                                {streamUrl
                                    ? 'The raw STF screen stream stays live here without the full control chrome.'
                                    : devices.length
                                      ? 'Choose a phone from the list to open it in the dashboard.'
                                      : 'The embedded viewer will appear here when a device is ready.'}
                            </CardDescription>
                        </CardHeader>

                        <CardContent className="bg-[radial-gradient(circle_at_top,#1f2937,transparent_45%),linear-gradient(180deg,#0f172a,#020617)] p-6">
                            <div className="mx-auto flex w-full max-w-[17rem] justify-center sm:max-w-[18rem] xl:max-w-[19rem]">
                                <div className="w-full rounded-[1.9rem] border border-white/10 bg-slate-950 p-3 shadow-[0_18px_56px_rgba(2,6,23,0.58)]">
                                    <div className="mx-auto mb-3 h-1.5 w-16 rounded-full bg-white/15" />
                                    <div className="relative aspect-[9/19.5] overflow-hidden rounded-[1.4rem] border border-white/10 bg-slate-900">
                                        {streamUrl ? (
                                            <>
                                                {stfSessionUrl ? (
                                                    <iframe
                                                        title="STF session bootstrap"
                                                        src={stfSessionUrl}
                                                        className="hidden"
                                                        tabIndex={-1}
                                                        aria-hidden="true"
                                                    />
                                                ) : null}
                                                <iframe
                                                    key={streamUrl}
                                                    title={`STF device ${device?.serial ?? 'viewer'}`}
                                                    src={streamUrl}
                                                    className="size-full border-0 bg-black"
                                                    allow="clipboard-read; clipboard-write"
                                                />
                                            </>
                                        ) : (
                                            <div className="flex size-full flex-col items-center justify-center gap-4 px-6 text-center text-slate-200">
                                                <div className="rounded-full border border-white/15 bg-white/5 p-4">
                                                    {error ? (
                                                        <TriangleAlert className="size-7 text-amber-300" />
                                                    ) : (
                                                        <Wifi className="size-7" />
                                                    )}
                                                </div>
                                                <div className="space-y-2">
                                                    <p className="text-base font-medium">
                                                        {error ?? (devices.length
                                                            ? 'Select a phone from the device list to open it.'
                                                            : 'Waiting for STF to return a device.')}
                                                    </p>
                                                    <p className="text-sm text-slate-400">
                                                        Refresh after STF is running and your phone is visible in
                                                        the device list.
                                                    </p>
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    <div className="space-y-6">
                        <Card className="border-sidebar-border/70 dark:border-sidebar-border">
                            <CardHeader>
                                <CardTitle>Available devices</CardTitle>
                                <CardDescription>
                                    Pick the phone you want to open in the dashboard.
                                </CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-3">
                                {devices.length ? (
                                    <div className="space-y-2">
                                        {devices.map((availableDevice) => {
                                            const isActive = selectedSerial === availableDevice.serial;
                                            const availableDeviceName =
                                                availableDevice.name ||
                                                [availableDevice.manufacturer, availableDevice.model]
                                                    .filter(Boolean)
                                                    .join(' ') ||
                                                availableDevice.model ||
                                                availableDevice.serial;

                                            return (
                                                <Button
                                                    key={availableDevice.serial}
                                                    variant={isActive ? 'default' : 'outline'}
                                                    className="h-auto w-full justify-between gap-4 px-4 py-3 text-left"
                                                    asChild
                                                >
                                                    <Link href={`/dashboard?serial=${encodeURIComponent(availableDevice.serial)}`}>
                                                        <span className="flex flex-col">
                                                            <span className="font-medium">{availableDeviceName}</span>
                                                            {canOpenStf ? (
                                                                <span className="text-xs text-muted-foreground">
                                                                    {availableDevice.serial}
                                                                </span>
                                                            ) : null}
                                                        </span>
                                                        <span className="flex gap-2">
                                                            <Badge variant={availableDevice.present ? 'default' : 'outline'}>
                                                                {availableDevice.present ? 'Present' : 'Offline'}
                                                            </Badge>
                                                            <Badge variant={availableDevice.ready ? 'default' : 'outline'}>
                                                                {availableDevice.ready ? 'Ready' : 'Busy'}
                                                            </Badge>
                                                        </span>
                                                    </Link>
                                                </Button>
                                            );
                                        })}
                                    </div>
                                ) : (
                                    <p className="text-sm text-muted-foreground">
                                        No STF devices are available yet.
                                    </p>
                                )}
                            </CardContent>
                        </Card>

                        <Card className="border-sidebar-border/70 dark:border-sidebar-border">
                            <CardHeader>
                                <CardTitle>Connected device</CardTitle>
                                <CardDescription>
                                    {canOpenStf
                                        ? 'Current metadata returned by the STF API.'
                                        : 'Basic details about the phone you are using.'}
                                </CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="flex flex-wrap gap-2">
                                    <Badge variant={device?.present ? 'default' : 'outline'}>
                                        {device?.present ? 'Present' : 'Not detected'}
                                    </Badge>
                                    <Badge variant={device?.ready ? 'default' : 'outline'}>
                                        {device?.ready ? 'Ready' : 'Not ready'}
                                    </Badge>
                                    {device?.using ? (
                                        <Badge variant="secondary">In use</Badge>
                                    ) : null}
                                </div>

                                <div className="rounded-xl border bg-muted/30 px-4 py-3 text-sm">
                                    <p className="font-medium">Audio routing</p>
                                    <p className="mt-1 text-muted-foreground">
                                        {audioStatus.message ?? 'Audio state unavailable.'}
                                    </p>
                                    <p className="mt-2 text-xs text-muted-foreground">
                                        Source: {audioStatus.source ?? 'output'}
                                        {audioStatus.pid ? ` • PID ${audioStatus.pid}` : ''}
                                    </p>
                                </div>

                                <dl className="space-y-3">
                                    {infoRows.map((row) => (
                                        <div
                                            key={row.label}
                                            className="flex items-center justify-between gap-4 border-b pb-3 text-sm last:border-b-0 last:pb-0"
                                        >
                                            <dt className="text-muted-foreground">{row.label}</dt>
                                            <dd className="text-right font-medium">{row.value}</dd>
                                        </div>
                                    ))}
                                </dl>
                            </CardContent>
                        </Card>

                        <Card className="border-sidebar-border/70 dark:border-sidebar-border">
                            <CardHeader>
                                <CardTitle>Quick checks</CardTitle>
                                <CardDescription>
                                    The most common reasons the phone view stays empty.
                                </CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-3 text-sm text-muted-foreground">
                                <p>1. Make sure STF is running at the URL from `STF_BASE_URL`.</p>
                                <p>2. Confirm `STF_TOKEN` is valid and can read `/api/v1/devices`.</p>
                                <p>3. Verify the phone appears in STF and is marked ready.</p>
                                <p>4. If taps do nothing, confirm the STF websocket unit is running on port `7110` or set `STF_WEBSOCKET_URL` explicitly.</p>
                            </CardContent>
                        </Card>
                    </div>
                </div>
            </div>
        </AppLayout>
    );
}
