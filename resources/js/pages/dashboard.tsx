import { Head, Link } from '@inertiajs/react';
import {
    ExternalLink,
    RefreshCcw,
    Smartphone,
    TriangleAlert,
    Wifi,
} from 'lucide-react';
import StfScreenViewer from '@/components/stf-screen-viewer';
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
    device: Device | null;
    error: string | null;
    stfBaseUrl: string;
    streamUrl: string | null;
};

const breadcrumbs: BreadcrumbItem[] = [
    {
        title: 'Live phone',
        href: dashboard(),
    },
];

export default function Dashboard({ device, error, stfBaseUrl, streamUrl }: Props) {
    const infoRows = [
        { label: 'Serial', value: device?.serial ?? 'Unavailable' },
        { label: 'Device', value: device?.name ?? device?.model ?? 'Unknown' },
        { label: 'Manufacturer', value: device?.manufacturer ?? 'Unknown' },
        { label: 'Platform', value: device?.platform ?? 'Android' },
        { label: 'Version', value: device?.version ?? 'Unknown' },
        { label: 'SDK', value: device?.sdk ? String(device.sdk) : 'Unknown' },
    ];

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

                        {stfBaseUrl ? (
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

                <div className="grid gap-6 xl:grid-cols-[minmax(0,1.4fr)_minmax(320px,0.8fr)]">
                    <Card className="overflow-hidden rounded-[2rem] border-sidebar-border/70 pt-0 dark:border-sidebar-border">
                        <CardHeader className="border-b bg-muted/40 px-6 py-5">
                            <CardTitle>Phone screen</CardTitle>
                            <CardDescription>
                                {streamUrl
                                    ? 'The raw STF screen stream stays live here without the full control chrome.'
                                    : 'The embedded viewer will appear here when a device is ready.'}
                            </CardDescription>
                        </CardHeader>

                        <CardContent className="bg-[radial-gradient(circle_at_top,#1f2937,transparent_45%),linear-gradient(180deg,#0f172a,#020617)] p-6">
                            <div className="mx-auto flex w-full max-w-md justify-center">
                                <div className="w-full rounded-[2.25rem] border border-white/10 bg-slate-950 p-4 shadow-[0_24px_80px_rgba(2,6,23,0.65)]">
                                    <div className="mx-auto mb-4 h-1.5 w-20 rounded-full bg-white/15" />
                                    <div className="relative aspect-[9/19.5] overflow-hidden rounded-[1.75rem] border border-white/10 bg-slate-900">
                                        {streamUrl && device?.display?.url ? (
                                            <StfScreenViewer
                                                websocketUrl={device.display.url}
                                                width={device.display.width}
                                                height={device.display.height}
                                            />
                                        ) : (
                                            <div className="flex size-full flex-col items-center justify-center gap-4 px-6 text-center text-slate-200">
                                                <div className="rounded-full border border-white/15 bg-white/5 p-4">
                                                    {error ? (
                                                        <TriangleAlert className="size-7 text-amber-300" />
                                                    ) : (
                                                        <Smartphone className="size-7" />
                                                    )}
                                                </div>
                                                <div className="space-y-2">
                                                    <p className="text-base font-medium">
                                                        {error ?? 'Waiting for STF to return a device.'}
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
                                <CardTitle>Connected device</CardTitle>
                                <CardDescription>
                                    Current metadata returned by the STF API.
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
                                <p>4. If the screen stream stays blank, open STF once in the browser and confirm the device works there too.</p>
                            </CardContent>
                        </Card>
                    </div>
                </div>
            </div>
        </AppLayout>
    );
}
