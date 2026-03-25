import { Head, useForm } from '@inertiajs/react';
import { CheckSquare, Mail, PencilLine, ShieldCheck, Smartphone, UserRound } from 'lucide-react';
import { useState } from 'react';
import InputError from '@/components/input-error';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';
import AppLayout from '@/layouts/app-layout';
import type { BreadcrumbItem } from '@/types';

type AdminUser = {
    assigned_serials: string[];
    id: number;
    name: string;
    email: string;
    role: 'admin' | 'user';
    email_verified_at: string | null;
    created_at: string;
};

type AvailablePhone = {
    label: string;
    present: boolean;
    ready: boolean;
    serial: string;
};

type Props = {
    availablePhones: AvailablePhone[];
    users: AdminUser[];
};

const breadcrumbs: BreadcrumbItem[] = [
    { title: 'Admin', href: '/admin' },
    { title: 'Users', href: '/admin/users' },
];

export default function AdminUsers({ availablePhones, users }: Props) {
    const [editingUserId, setEditingUserId] = useState<number | null>(null);

    return (
        <AppLayout breadcrumbs={breadcrumbs}>
            <Head title="Admin Users" />

            <div className="flex h-full flex-1 flex-col gap-6 rounded-xl p-4">
                <Card className="border-sidebar-border/70 dark:border-sidebar-border">
                    <CardHeader>
                        <CardTitle>User management</CardTitle>
                        <CardDescription>
                            Edit account details and roles from one admin-only workspace.
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        {users.length ? (
                            <div className="grid gap-4 md:grid-cols-2 2xl:grid-cols-4">
                                {users.map((user) => (
                                    <EditableUserCard
                                        availablePhones={availablePhones}
                                        key={user.id}
                                        user={user}
                                        isEditing={editingUserId === user.id}
                                        onEdit={() => setEditingUserId(user.id)}
                                        onCancel={() => setEditingUserId(null)}
                                        onSaved={() => setEditingUserId(null)}
                                    />
                                ))}
                            </div>
                        ) : (
                            <p className="text-sm text-muted-foreground">No users found.</p>
                        )}
                    </CardContent>
                </Card>
            </div>
        </AppLayout>
    );
}

function EditableUserCard({
    availablePhones,
    user,
    isEditing,
    onCancel,
    onEdit,
    onSaved,
}: {
    availablePhones: AvailablePhone[];
    user: AdminUser;
    isEditing: boolean;
    onCancel: () => void;
    onEdit: () => void;
    onSaved: () => void;
}) {
    const form = useForm({
        assigned_serials: user.assigned_serials,
        name: user.name,
        email: user.email,
        role: user.role,
    });

    const togglePhone = (serial: string) => {
        form.setData(
            'assigned_serials',
            form.data.assigned_serials.includes(serial)
                ? form.data.assigned_serials.filter((value) => value !== serial)
                : [...form.data.assigned_serials, serial],
        );
    };

    const submit = (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();

        form.patch(`/admin/users/${user.id}`, {
            preserveScroll: true,
            onSuccess: () => {
                onSaved();
            },
        });
    };

    return (
        <div className="overflow-hidden rounded-3xl border bg-card shadow-sm">
            <div className="flex min-h-72 flex-col bg-muted/20">
                <div className="flex items-start justify-between gap-3 border-b bg-muted/30 px-4 py-4">
                    <div className="min-w-0 space-y-3">
                        <div className="space-y-1">
                            <p className="truncate text-base font-semibold">{user.name}</p>
                            <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                <Mail className="size-4 shrink-0" />
                                <span className="truncate">{user.email}</span>
                            </div>
                        </div>
                        <div className="flex flex-wrap gap-2">
                            <Badge variant={user.role === 'admin' ? 'default' : 'outline'}>
                                {user.role === 'admin' ? (
                                    <ShieldCheck className="mr-1 size-3.5" />
                                ) : (
                                    <UserRound className="mr-1 size-3.5" />
                                )}
                                {user.role}
                            </Badge>
                            <Badge variant="outline">
                                {user.email_verified_at ? 'Verified' : 'Unverified'}
                            </Badge>
                            <Badge variant="outline">
                                <Smartphone className="mr-1 size-3.5" />
                                {user.assigned_serials.length} phones
                            </Badge>
                        </div>
                    </div>

                    <Button
                        size="sm"
                        variant={isEditing ? 'secondary' : 'outline'}
                        onClick={isEditing ? onCancel : onEdit}
                    >
                        <PencilLine className="size-4" />
                        {isEditing ? 'Close' : 'Edit'}
                    </Button>
                </div>

                {isEditing ? (
                    <form onSubmit={submit} className="grid flex-1 gap-4 px-4 py-4">
                        <div className="space-y-2">
                            <Label htmlFor={`name-${user.id}`}>Name</Label>
                            <Input
                                id={`name-${user.id}`}
                                value={form.data.name}
                                onChange={(event) => form.setData('name', event.target.value)}
                                placeholder="Full name"
                            />
                            <InputError message={form.errors.name} />
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor={`email-${user.id}`}>Email</Label>
                            <Input
                                id={`email-${user.id}`}
                                type="email"
                                value={form.data.email}
                                onChange={(event) => form.setData('email', event.target.value)}
                                placeholder="Email address"
                            />
                            <InputError message={form.errors.email} />
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor={`role-${user.id}`}>Role</Label>
                            <Select
                                value={form.data.role}
                                onValueChange={(value) => form.setData('role', value as 'admin' | 'user')}
                            >
                                <SelectTrigger id={`role-${user.id}`} className="w-full">
                                    <SelectValue placeholder="Select a role" />
                                </SelectTrigger>
                                <SelectContent align="start">
                                    <SelectItem value="admin">Admin</SelectItem>
                                    <SelectItem value="user">User</SelectItem>
                                </SelectContent>
                            </Select>
                            <InputError message={form.errors.role} />
                        </div>

                        <div className="space-y-3">
                            <div className="space-y-1">
                                <Label>Phone access</Label>
                                <p className="text-sm text-muted-foreground">
                                    Assign which STF phones this user can open.
                                </p>
                            </div>

                            {availablePhones.length ? (
                                <div className="grid gap-2">
                                    {availablePhones.map((phone) => {
                                        const checked = form.data.assigned_serials.includes(phone.serial);

                                        return (
                                            <button
                                                key={phone.serial}
                                                type="button"
                                                onClick={() => togglePhone(phone.serial)}
                                                className={`flex items-center justify-between gap-3 rounded-2xl border px-3 py-2 text-left transition-colors ${
                                                    checked
                                                        ? 'border-primary bg-primary/5'
                                                        : 'border-border bg-background'
                                                }`}
                                            >
                                                <div className="min-w-0 space-y-1">
                                                    <p className="truncate text-sm font-medium">{phone.label}</p>
                                                    <p className="truncate text-xs text-muted-foreground">
                                                        {phone.serial}
                                                    </p>
                                                </div>
                                                <div className="flex shrink-0 items-center gap-2">
                                                    <Badge variant={phone.present ? 'default' : 'outline'}>
                                                        {phone.present ? 'Present' : 'Offline'}
                                                    </Badge>
                                                    <Badge variant={phone.ready ? 'default' : 'outline'}>
                                                        {phone.ready ? 'Ready' : 'Busy'}
                                                    </Badge>
                                                    <CheckSquare
                                                        className={`size-4 ${checked ? 'text-primary' : 'text-muted-foreground'}`}
                                                    />
                                                </div>
                                            </button>
                                        );
                                    })}
                                </div>
                            ) : (
                                <p className="rounded-2xl border bg-background/80 px-3 py-2 text-sm text-muted-foreground">
                                    No STF phones are available right now.
                                </p>
                            )}

                            <InputError message={form.errors.assigned_serials} />
                        </div>

                        <div className="mt-auto flex items-center gap-3 pt-2">
                            <Button type="submit" size="sm" disabled={form.processing}>
                                Save
                            </Button>
                            <Button type="button" size="sm" variant="ghost" onClick={onCancel}>
                                Cancel
                            </Button>
                            {form.recentlySuccessful ? (
                                <p className="text-sm text-muted-foreground">Saved</p>
                            ) : null}
                        </div>
                    </form>
                ) : (
                    <div className="grid flex-1 content-start gap-3 px-4 py-4 text-sm text-muted-foreground">
                        <p className="rounded-2xl border bg-background/80 px-3 py-2">
                            <span className="font-medium text-foreground">Role:</span> {user.role}
                        </p>
                        <p className="rounded-2xl border bg-background/80 px-3 py-2">
                            <span className="font-medium text-foreground">Email:</span>{' '}
                            {user.email_verified_at ? 'Verified' : 'Unverified'}
                        </p>
                        <p className="rounded-2xl border bg-background/80 px-3 py-2">
                            <span className="font-medium text-foreground">User ID:</span> {user.id}
                        </p>
                        <p className="rounded-2xl border bg-background/80 px-3 py-2">
                            <span className="font-medium text-foreground">Phone access:</span>{' '}
                            {user.assigned_serials.length ? user.assigned_serials.join(', ') : 'None assigned'}
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
}
