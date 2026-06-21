import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '@/shared/hooks/useAuth';
import { authApi } from '@/api/auth';
import { UserRole } from '@/types/index';
import { Button, Card, Input, Select, SectionHeading } from '@/shared/ui';
import { useI18n, type Locale } from '@/shared/i18n';
import { useT } from '@/shared/i18n/useT';
import { usePushSubscription } from '@/features/pwa/usePushSubscription';
import type { AxiosError } from 'axios';

function extractError(err: unknown, fallback = 'Save failed. Please try again.'): string {
  const axiosErr = err as AxiosError<Record<string, string[] | string>>;
  const data = axiosErr?.response?.data;
  if (!data) return fallback;
  const firstKey = Object.keys(data)[0];
  if (firstKey && Array.isArray(data[firstKey])) return data[firstKey][0];
  if (firstKey && typeof data[firstKey] === 'string') return data[firstKey];
  return fallback;
}

export const ProfilePage = () => {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const { setLocale } = useI18n();
  const t = useT();
  const push = usePushSubscription();

  const [form, setForm] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone_number: '',
  });
  const [emailRemindersOptOut, setEmailRemindersOptOut] = useState(false);
  const [preferredLanguage, setPreferredLanguage] = useState<Locale>('en');
  const [savedMsg, setSavedMsg] = useState(false);
  const [passwordForm, setPasswordForm] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });
  const [passwordSavedMsg, setPasswordSavedMsg] = useState(false);

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
      setPreferredLanguage(user.preferred_language ?? 'en');
    }
  }

  const mutation = useMutation({
    mutationFn: authApi.updateProfile,
    onSuccess: async (updated) => {
      await queryClient.invalidateQueries({ queryKey: ['auth'] });
      // Apply the saved language preference to the live UI immediately.
      if (updated.preferred_language) setLocale(updated.preferred_language);
      setSavedMsg(true);
      setTimeout(() => setSavedMsg(false), 3000);
    },
  });

  const passwordMutation = useMutation({
    mutationFn: authApi.changePassword,
    onSuccess: () => {
      setPasswordForm({ current_password: '', new_password: '', confirm_password: '' });
      setPasswordSavedMsg(true);
      setTimeout(() => setPasswordSavedMsg(false), 3000);
    },
  });

  const set = (field: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((prev) => ({ ...prev, [field]: e.target.value }));

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const payload = { ...form, preferred_language: preferredLanguage };
    mutation.mutate(
      isStudent ? { ...payload, email_reminders_opt_out: emailRemindersOptOut } : payload
    );
  };

  const setPassword = (field: keyof typeof passwordForm) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setPasswordForm((prev) => ({ ...prev, [field]: e.target.value }));

  const handlePasswordSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (passwordForm.new_password !== passwordForm.confirm_password) return;
    passwordMutation.mutate({
      current_password: passwordForm.current_password,
      new_password: passwordForm.new_password,
    });
  };

  const passwordMismatch =
    passwordForm.confirm_password.length > 0 &&
    passwordForm.new_password !== passwordForm.confirm_password;

  return (
    <div className="max-w-xl space-y-6">
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

            <Select
              label="Language / भाषा"
              id="preferred_language"
              value={preferredLanguage}
              onChange={(e) => setPreferredLanguage(e.target.value as Locale)}
              disabled={mutation.isPending}
              hint="Your preference follows you across devices."
            >
              <option value="en">English</option>
              <option value="hi" lang="hi">
                हिंदी (Hindi)
              </option>
            </Select>

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

                {push.supported && (
                  <label className="flex items-start gap-3 cursor-pointer mt-4">
                    <input
                      type="checkbox"
                      checked={push.isSubscribed}
                      disabled={push.busy || push.permission === 'denied'}
                      onChange={(e) =>
                        e.target.checked ? push.subscribe() : push.unsubscribe()
                      }
                      className="mt-0.5 w-4 h-4 rounded border-ink-300 text-brand-600 focus:ring-brand-500"
                    />
                    <span>
                      <span className="block text-sm font-medium text-ink-900">
                        {t('push.label')}
                      </span>
                      <span className="block text-xs text-ink-500 mt-0.5">
                        {push.permission === 'denied' ? t('push.blocked') : t('push.description')}
                      </span>
                    </span>
                  </label>
                )}
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

      <Card>
        <form onSubmit={handlePasswordSubmit} noValidate>
          <div className="space-y-4">
            <div>
              <h2 className="font-display text-lg font-semibold text-ink-900">Change password</h2>
              <p className="mt-1 text-sm text-ink-500">
                Use a fresh password that you do not use on other sites.
              </p>
            </div>

            <Input
              label="Current password"
              id="current_password"
              type="password"
              value={passwordForm.current_password}
              onChange={setPassword('current_password')}
              disabled={passwordMutation.isPending}
              autoComplete="current-password"
            />

            <Input
              label="New password"
              id="new_password"
              type="password"
              value={passwordForm.new_password}
              onChange={setPassword('new_password')}
              disabled={passwordMutation.isPending}
              autoComplete="new-password"
            />

            <Input
              label="Confirm new password"
              id="confirm_password"
              type="password"
              value={passwordForm.confirm_password}
              onChange={setPassword('confirm_password')}
              disabled={passwordMutation.isPending}
              autoComplete="new-password"
              error={passwordMismatch ? 'Passwords do not match.' : undefined}
            />

            {passwordMutation.isError && (
              <div className="rounded-lg bg-rose-50 border border-rose-200 px-4 py-3 text-sm text-rose-700" role="alert">
                {extractError(passwordMutation.error, 'Password change failed. Please try again.')}
              </div>
            )}

            {passwordSavedMsg && (
              <div className="rounded-lg bg-emerald-50 border border-emerald-200 px-4 py-3 text-sm text-emerald-700" role="status">
                Password changed successfully.
              </div>
            )}

            <div className="flex justify-end pt-2">
              <Button
                type="submit"
                disabled={
                  passwordMutation.isPending ||
                  !passwordForm.current_password ||
                  !passwordForm.new_password ||
                  !passwordForm.confirm_password ||
                  passwordMismatch
                }
              >
                {passwordMutation.isPending ? 'Updating...' : 'Update Password'}
              </Button>
            </div>
          </div>
        </form>
      </Card>
    </div>
  );
};
