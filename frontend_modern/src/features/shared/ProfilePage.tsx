import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '@/shared/hooks/useAuth';
import { authApi } from '@/api/auth';
import { UserRole } from '@/types/index';
import { Button, Card, Input, SectionHeading } from '@/shared/ui';
import type { AxiosError } from 'axios';

function extractError(err: unknown): string {
  const axiosErr = err as AxiosError<Record<string, string[]>>;
  const data = axiosErr?.response?.data;
  if (!data) return 'Save failed. Please try again.';
  const firstKey = Object.keys(data)[0];
  if (firstKey && Array.isArray(data[firstKey])) return data[firstKey][0];
  return 'Save failed. Please try again.';
}

export const ProfilePage = () => {
  const { user } = useAuth();
  const queryClient = useQueryClient();

  const [form, setForm] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone_number: '',
  });
  const [emailRemindersOptOut, setEmailRemindersOptOut] = useState(false);
  const [savedMsg, setSavedMsg] = useState(false);

  const isStudent = user?.role === UserRole.STUDENT || user?.role === UserRole.OPEN_STUDENT;

  // Sync the form when the loaded user changes (during render — react.dev/learn/you-might-not-need-an-effect)
  const [syncedUser, setSyncedUser] = useState<typeof user | undefined>(undefined);
  if (user !== syncedUser) {
    setSyncedUser(user);
    if (user) {
      setForm({
        first_name: user.first_name ?? '',
        last_name: user.last_name ?? '',
        email: user.email ?? '',
        phone_number: user.phone_number ?? '',
      });
      setEmailRemindersOptOut(user.email_reminders_opt_out ?? false);
    }
  }

  const mutation = useMutation({
    mutationFn: authApi.updateProfile,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['auth'] });
      setSavedMsg(true);
      setTimeout(() => setSavedMsg(false), 3000);
    },
  });

  const set = (field: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((prev) => ({ ...prev, [field]: e.target.value }));

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    mutation.mutate(
      isStudent ? { ...form, email_reminders_opt_out: emailRemindersOptOut } : form
    );
  };

  return (
    <div className="max-w-xl">
      <SectionHeading as="h1" title="Profile Settings" className="mb-6" />

      <Card>
        {user && (
          <div className="flex items-center gap-4 mb-6 pb-6 border-b border-ink-100">
            <div className="w-12 h-12 bg-brand-100 rounded-full flex items-center justify-center">
              <span className="text-brand-700 font-bold text-lg font-display">
                {(user.first_name?.[0] ?? user.username[0]).toUpperCase()}
              </span>
            </div>
            <div>
              <p className="font-semibold text-ink-900">{user.username}</p>
              <p className="text-sm text-ink-500 capitalize">{user.role.replace('_', ' ')}</p>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} noValidate>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <Input
                label="First Name"
                id="first_name"
                value={form.first_name}
                onChange={set('first_name')}
                disabled={mutation.isPending}
                autoComplete="given-name"
              />
              <Input
                label="Last Name"
                id="last_name"
                value={form.last_name}
                onChange={set('last_name')}
                disabled={mutation.isPending}
                autoComplete="family-name"
              />
            </div>

            <Input
              label="Email"
              id="email"
              type="email"
              value={form.email}
              onChange={set('email')}
              disabled={mutation.isPending}
              autoComplete="email"
              placeholder="your@email.com"
            />

            <Input
              label="Phone Number"
              id="phone_number"
              value={form.phone_number}
              onChange={set('phone_number')}
              disabled={mutation.isPending}
              autoComplete="tel"
              placeholder="+91 9876543210"
            />

            {isStudent && (
              <div className="pt-2 border-t border-ink-100">
                <label className="flex items-start gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={!emailRemindersOptOut}
                    onChange={(e) => setEmailRemindersOptOut(!e.target.checked)}
                    disabled={mutation.isPending}
                    className="mt-0.5 w-4 h-4 rounded border-ink-300 text-brand-600 focus:ring-brand-500"
                  />
                  <span>
                    <span className="block text-sm font-medium text-ink-900">
                      Assignment due-date reminders
                    </span>
                    <span className="block text-xs text-ink-500 mt-0.5">
                      Email me before an assignment is due. Uncheck to stop these reminders.
                    </span>
                  </span>
                </label>
              </div>
            )}

            {mutation.isError && (
              <div className="rounded-lg bg-rose-50 border border-rose-200 px-4 py-3 text-sm text-rose-700" role="alert">
                {extractError(mutation.error)}
              </div>
            )}

            {savedMsg && (
              <div className="rounded-lg bg-emerald-50 border border-emerald-200 px-4 py-3 text-sm text-emerald-700" role="status">
                Profile saved successfully.
              </div>
            )}

            <div className="flex justify-end pt-2">
              <Button type="submit" disabled={mutation.isPending}>
                {mutation.isPending ? 'Saving…' : 'Save Changes'}
              </Button>
            </div>
          </div>
        </form>
      </Card>
    </div>
  );
};
