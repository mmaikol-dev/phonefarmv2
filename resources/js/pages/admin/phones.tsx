import { Head, Link } from '@inertiajs/react';
import { ExternalLink, MoreHorizontal, TriangleAlert } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import AppLayout from '@/layouts/app-layout';
import type { BreadcrumbItem } from '@/types';

type Device = {
    serial: string;
    name?: string;
    model?: string;
    manufacturer?: string;
    present?: boolean;
    ready?: boolean;
    using?: boolean;
    platform?: string;
    version?: string;
    streamUrl?: string;
};

type Props = {
    devices: Device[];
    error: string | null;
    stfSessionUrl: string | null;
};

const breadcrumbs: BreadcrumbItem[] = [
    { title: 'Admin', href: '/admin' },
    { title: 'Phones', href: '/admin/phones' },
];

export default function AdminPhones({ devices, error, stfSessionUrl }: Props) {
    return (
        <AppLayout breadcrumbs={breadcrumbs}>
            <Head title="Admin Phones" />

            <div className="flex h-full min-h-0 flex-1 flex-col gap-6 rounded-xl p-4">
                {stfSessionUrl ? (
                    <iframe
                        title="STF session bootstrap"
                        src={stfSessionUrl}
                        className="hidden"
                        tabIndex={-1}
                        aria-hidden="true"
                    />
                ) : null}

                <Card className="flex min-h-0 flex-1 flex-col border-sidebar-border/70 dark:border-sidebar-border">
                    <CardHeader className="flex flex-row items-center justify-between gap-4">
                        <div>
                            <CardTitle>Phone wall</CardTitle>
                            <CardDescription>
                                {devices.length} {devices.length === 1 ? 'device' : 'devices'} reported by STF.
                            </CardDescription>
                        </div>
                        <Button variant="outline" asChild>
                            <Link href="/admin/phones">Refresh</Link>
                        </Button>
                    </CardHeader>
                    <CardContent className="min-h-0 flex-1 space-y-3 overflow-hidden">
                        {error ? (
                            <div className="flex items-start gap-3 rounded-2xl border border-amber-300/50 bg-amber-50 px-4 py-3 text-sm text-amber-900 dark:border-amber-500/40 dark:bg-amber-950/20 dark:text-amber-200">
                                <TriangleAlert className="mt-0.5 size-4 shrink-0" />
                                <p>{error}</p>
                            </div>
                        ) : null}

                        {devices.length ? (
                            <div className="h-[70vh] overflow-y-auto pr-2">
                                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5">
                                {devices.map((device) => (
                                    <div
                                        key={device.serial}
                                        className="overflow-hidden rounded-2xl border bg-card"
                                    >
                                        <div className="border-b px-3 py-3">
                                            <div className="flex items-start justify-between gap-3">
                                                <div className="space-y-1">
                                                    <p className="truncate text-sm font-medium">
                                                        {device.name ?? device.model ?? device.serial}
                                                    </p>
                                                    <p className="truncate text-xs text-muted-foreground">
                                                        {device.manufacturer ?? 'Unknown'} • {device.serial}
                                                    </p>
                                                </div>

                                                <DropdownMenu>
                                                    <DropdownMenuTrigger asChild>
                                                        <Button
                                                            size="icon"
                                                            variant="outline"
                                                            className="size-8 shrink-0"
                                                        >
                                                            <MoreHorizontal className="size-4" />
                                                        </Button>
                                                    </DropdownMenuTrigger>
                                                    <DropdownMenuContent align="end" className="w-44">
                                                        <DropdownMenuLabel>Phone actions</DropdownMenuLabel>
                                                        <DropdownMenuSeparator />
                                                        <DropdownMenuItem asChild>
                                                            <Link href={`/dashboard?serial=${encodeURIComponent(device.serial)}`}>
                                                                Open
                                                                <ExternalLink className="ml-auto size-4" />
                                                            </Link>
                                                        </DropdownMenuItem>
                                                        <DropdownMenuItem disabled>
                                                            Present
                                                            <span className="ml-auto text-xs text-muted-foreground">
                                                                {device.present ? 'Yes' : 'No'}
                                                            </span>
                                                        </DropdownMenuItem>
                                                        <DropdownMenuItem disabled>
                                                            Ready
                                                            <span className="ml-auto text-xs text-muted-foreground">
                                                                {device.ready ? 'Yes' : 'No'}
                                                            </span>
                                                        </DropdownMenuItem>
                                                        <DropdownMenuItem disabled>
                                                            In use
                                                            <span className="ml-auto text-xs text-muted-foreground">
                                                                {device.using ? 'Yes' : 'No'}
                                                            </span>
                                                        </DropdownMenuItem>
                                                    </DropdownMenuContent>
                                                </DropdownMenu>
                                            </div>
                                        </div>

                                        <div className="bg-[radial-gradient(circle_at_top,#1f2937,transparent_45%),linear-gradient(180deg,#0f172a,#020617)] px-3 py-3">
                                            <div className="mx-auto w-full max-w-[10.75rem] rounded-[1.2rem] border border-white/10 bg-slate-950 p-2 shadow-[0_14px_40px_rgba(2,6,23,0.38)]">
                                                <div className="mx-auto mb-2 h-1 w-10 rounded-full bg-white/15" />
                                                <div className="relative aspect-[9/19.5] overflow-hidden rounded-[0.9rem] border border-white/10 bg-slate-900">
                                                    {device.streamUrl ? (
                                                        <iframe
                                                            title={`Admin STF device ${device.serial}`}
                                                            src={device.streamUrl}
                                                            className="size-full border-0 bg-black"
                                                            allow="clipboard-read; clipboard-write"
                                                        />
                                                    ) : (
                                                        <div className="flex size-full items-center justify-center px-4 text-center text-xs text-slate-300">
                                                            Screen unavailable
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                        </div>

                                        <div className="px-3 py-2 text-xs text-muted-foreground">
                                            {device.platform ?? 'Android'} {device.version ?? ''}
                                        </div>
                                    </div>
                                ))}
                                </div>
                            </div>
                        ) : (
                            <p className="text-sm text-muted-foreground">
                                No phones are currently available.
                            </p>
                        )}
                    </CardContent>
                </Card>
            </div>
        </AppLayout>
    );
}
