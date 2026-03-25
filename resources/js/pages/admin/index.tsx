import { Head, Link } from '@inertiajs/react';
import { ShieldCheck, Smartphone, Users } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import AppLayout from '@/layouts/app-layout';
import type { BreadcrumbItem } from '@/types';

type Props = {
    links: {
        description: string;
        href: string;
        title: string;
    }[];
};

const breadcrumbs: BreadcrumbItem[] = [
    {
        title: 'Admin',
        href: '/admin',
    },
];

export default function AdminIndex({ links }: Props) {
    return (
        <AppLayout breadcrumbs={breadcrumbs}>
            <Head title="Admin" />

            <div className="flex h-full flex-1 flex-col gap-6 rounded-xl p-4">
                <div className="space-y-3 rounded-3xl border border-sidebar-border/70 bg-linear-to-br from-background via-background to-muted/30 p-6 shadow-sm dark:border-sidebar-border">
                    <Badge variant="outline" className="gap-1.5">
                        <ShieldCheck className="size-3.5" />
                        Admin access
                    </Badge>
                    <div className="space-y-2">
                        <h1 className="text-3xl font-semibold tracking-tight">Admin console</h1>
                        <p className="max-w-2xl text-sm text-muted-foreground">
                            This area is only available to admin users. Use it for protected
                            tools, user management, and system-level controls as the project grows.
                        </p>
                    </div>
                </div>

                <Card className="border-sidebar-border/70 dark:border-sidebar-border">
                    <CardHeader>
                        <CardTitle>Admin tools</CardTitle>
                        <CardDescription>
                            Protected areas only visible to admin users.
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-3">
                        {links.map((link) => (
                            <Link
                                key={link.href}
                                href={link.href}
                                className="flex items-start gap-3 rounded-2xl border p-4 transition-colors hover:bg-muted/40"
                            >
                                {link.title === 'Users' ? (
                                    <Users className="mt-0.5 size-4 shrink-0" />
                                ) : (
                                    <Smartphone className="mt-0.5 size-4 shrink-0" />
                                )}
                                <div className="space-y-1">
                                    <p className="font-medium">{link.title}</p>
                                    <p className="text-sm text-muted-foreground">{link.description}</p>
                                </div>
                            </Link>
                        ))}
                        <div className="flex items-start gap-3 rounded-2xl border p-4 text-sm text-muted-foreground">
                            <ShieldCheck className="mt-0.5 size-4 shrink-0" />
                            <p>The first registered user becomes admin automatically, and `ADMIN_EMAILS` can promote future accounts.</p>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </AppLayout>
    );
}
