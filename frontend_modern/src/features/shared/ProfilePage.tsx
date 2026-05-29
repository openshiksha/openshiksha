import { useEffect, useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '@/shared/hooks/useAuth';
import { authApi } from '@/api/auth';
import { UserRole } from '@/types/index';
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

  useEffect(() => {
    if (user) {
      setForm({
        first_name: user.first_name ?? '',
        last_name: user.last_name ?? '',
        email: user.email ?? '',
        phone_number: user.phone_number ?? '',
      });
      setEmailRemindersOptOut(user.email_reminders_opt_out ?? false);
    }
  }, [user]);

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
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Profile Settings</h1>

      <div className="bg-white rounded-xl border border-gray-200 p-6">
        {user && (
          <div className="flex items-center gap-4 mb-6 pb-6 border-b border-gray-100">
            <div className="w-12 h-12 bg-indigo-100 rounded-full flex items-center justify-center">
              <span className="text-indigo-700 font-bold text-lg">
                {(user.first_name?.[0] ?? user.username[0]).toUpperCase()}
              </span>
            </div>
            <div>
              <p className="font-semibold text-gray-900">{user.username}</p>
              <p className="text-sm text-gray-500 capitalize">{user.role.replace('_', ' ')}</p>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} noValidate>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <FormField
                label="First Name"
                id="first_name"
                value={form.first_name}
                onChange={set('first_name')}
                disabled={mutation.isPending}
                autoComplete="given-name"
              />
              <FormField
                label="Last Name"
                id="last_name"
                value={form.last_name}
                onChange={set('last_name')}
                disabled={mutation.isPending}
                autoComplete="family-name"
              />
            </div>

            <FormField
              label="Email"
              id="email"
              type="email"
              value={form.email}
              onChange={set('email')}
              disabled={mutation.isPending}
              autoComplete="email"
              placeholder="your@email.com"
            />

            <FormField
              label="Phone Number"
              id="phone_number"
              value={form.phone_number}
              onChange={set('phone_number')}
              disabled={mutation.isPending}
              autoComplete="tel"
              placeholder="+91 9876543210"
            />

            {isStudent && (
              <div className="pt-2 border-t border-gray-100">
                <label className="flex items-start gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={!emailRemindersOptOut}
                    onChange={(e) => setEmailRemindersOptOut(!e.target.checked)}
                    disabled={mutation.isPending}
                    className="mt-0.5 w-4 h-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                  />
                  <span>
                    <span className="block text-sm font-medium text-gray-900">
                      Assignment due-date reminders
                    </span>
                    <span className="block text-xs text-gray-500 mt-0.5">
                      Email me before an assignment is due. Uncheck to stop these reminders.
                    </span>
                  </span>
                </label>
              </div>
            )}

            {mutation.isError && (
              <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700" role="alert">
                {extractError(mutation.error)}
              </div>
            )}

            {savedMsg && (
              <div className="rounded-lg bg-green-50 border border-green-200 px-4 py-3 text-sm text-green-700" role="status">
                Profile saved successfully.
              </div>
            )}

            <div className="flex justify-end pt-2">
              <button
                type="submit"
                disabled={mutation.isPending}
                className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white font-semibold rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
              >
                {mutation.isPending ? 'Saving…' : 'Save Changes'}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};

interface FormFieldProps {
  label: string;
  id: string;
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  type?: string;
  disabled?: boolean;
  autoComplete?: string;
  placeholder?: string;
}

const FormField = ({ label, id, value, onChange, type = 'text', disabled, autoComplete, placeholder }: FormFieldProps) => (
  <div>
    <label htmlFor={id} className="block text-sm font-medium text-gray-700 mb-1">
      {label}
    </label>
    <input
      id={id}
      type={type}
      value={value}
      onChange={onChange}
      disabled={disabled}
      autoComplete={autoComplete}
      placeholder={placeholder}
      className="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-gray-900 placeholder-gray-400 disabled:bg-gray-50 disabled:text-gray-500"
    />
  </div>
);
