import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Button, Input } from '@/shared/ui';
import { AuthLayout } from './AuthLayout';
import { useRegisterOpenMutation } from './useRegisterMutation';
import type { AxiosError } from 'axios';

function extractError(err: unknown): string {
  const axiosErr = err as AxiosError<Record<string, string[]>>;
  const data = axiosErr?.response?.data;
  if (!data) return 'Registration failed. Please try again.';
  const firstKey = Object.keys(data)[0];
  if (firstKey && Array.isArray(data[firstKey])) return data[firstKey][0];
  return 'Registration failed. Please try again.';
}

export const RegisterOpenPage = () => {
  const mutation = useRegisterOpenMutation();
  const [form, setForm] = useState({
    first_name: '',
    last_name: '',
    username: '',
    password: '',
    email: '',
  });

  const set = (field: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((prev) => ({ ...prev, [field]: e.target.value }));

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    mutation.mutate({
      username: form.username,
      password: form.password,
      first_name: form.first_name || undefined,
      last_name: form.last_name || undefined,
      email: form.email || undefined,
    });
  };

  const disabled = mutation.isPending;

  return (
    <AuthLayout
      title="Study independently"
      subtitle="Access the shared question bank for free."
      footer={
        <p>
          <Link to="/register" className="font-semibold text-brand-700 hover:text-brand-800">
            ← Back
          </Link>
          {' · '}
          <Link to="/login" className="font-semibold text-brand-700 hover:text-brand-800">
            Sign in
          </Link>
        </p>
      }
    >
      <form onSubmit={handleSubmit} noValidate className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <Input label="First name" id="first_name" value={form.first_name} onChange={set('first_name')} disabled={disabled} />
          <Input label="Last name" id="last_name" value={form.last_name} onChange={set('last_name')} disabled={disabled} />
        </div>

        <Input label="Username" id="username" value={form.username} onChange={set('username')} required disabled={disabled} autoComplete="username" />
        <Input label="Password" id="password" type="password" value={form.password} onChange={set('password')} required disabled={disabled} autoComplete="new-password" />
        <Input label="Email (optional)" id="email" type="email" value={form.email} onChange={set('email')} disabled={disabled} autoComplete="email" />

        {mutation.isError && (
          <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700" role="alert">
            {extractError(mutation.error)}
          </div>
        )}

        <Button
          type="submit"
          size="lg"
          disabled={disabled || !form.username || !form.password}
          className="w-full"
        >
          {disabled ? 'Creating account…' : 'Start practising'}
        </Button>
      </form>
    </AuthLayout>
  );
};
