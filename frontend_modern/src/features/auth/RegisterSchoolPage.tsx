import { useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { Button, Input } from '@/shared/ui';
import { useT } from '@/shared/i18n';
import { AuthLayout } from './AuthLayout';
import { useRegisterSchoolMutation } from './useRegisterMutation';
import type { AxiosError } from 'axios';

function extractError(err: unknown, fallback: string): string {
  const axiosErr = err as AxiosError<Record<string, string[]>>;
  const data = axiosErr?.response?.data;
  if (!data) return fallback;
  const firstKey = Object.keys(data)[0];
  if (firstKey && Array.isArray(data[firstKey])) return data[firstKey][0];
  return fallback;
}

export const RegisterSchoolPage = () => {
  const t = useT();
  const mutation = useRegisterSchoolMutation();
  const [searchParams] = useSearchParams();
  const prefillCode = (searchParams.get('code') ?? '').toUpperCase().slice(0, 8);
  const [form, setForm] = useState({
    first_name: '',
    last_name: '',
    username: '',
    password: '',
    email: '',
    join_code: prefillCode,
  });

  const set = (field: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((prev) => ({ ...prev, [field]: e.target.value }));

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    mutation.mutate({
      username: form.username,
      password: form.password,
      first_name: form.first_name,
      last_name: form.last_name,
      email: form.email || undefined,
      join_code: form.join_code.toUpperCase(),
    });
  };

  const disabled = mutation.isPending;

  return (
    <AuthLayout
      title={t('register.schoolTitle')}
      subtitle={t('register.schoolSubtitle')}
      footer={
        <p>
          <Link to="/register" className="font-semibold text-brand-700 hover:text-brand-800">
            {t('register.back')}
          </Link>
          {' · '}
          <Link to="/login" className="font-semibold text-brand-700 hover:text-brand-800">
            {t('register.signIn')}
          </Link>
        </p>
      }
    >
      <form onSubmit={handleSubmit} noValidate className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <Input label={t('register.firstName')} id="first_name" value={form.first_name} onChange={set('first_name')} disabled={disabled} />
          <Input label={t('register.lastName')} id="last_name" value={form.last_name} onChange={set('last_name')} disabled={disabled} />
        </div>

        <Input label={t('register.username')} id="username" value={form.username} onChange={set('username')} required disabled={disabled} autoComplete="username" />
        <Input label={t('register.password')} id="password" type="password" value={form.password} onChange={set('password')} required disabled={disabled} autoComplete="new-password" />
        <Input label={t('register.emailOptional')} id="email" type="email" value={form.email} onChange={set('email')} disabled={disabled} autoComplete="email" />

        <Input
          label={t('register.joinCode')}
          id="join_code"
          value={form.join_code}
          onChange={set('join_code')}
          required
          disabled={disabled}
          placeholder={t('register.joinCodePlaceholder')}
          maxLength={8}
          className="font-mono uppercase tracking-widest placeholder:font-sans placeholder:tracking-normal placeholder:normal-case"
        />

        {mutation.isError && (
          <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700" role="alert">
            {extractError(mutation.error, t('register.error'))}
          </div>
        )}

        <Button
          type="submit"
          size="lg"
          disabled={disabled || !form.username || !form.password || !form.join_code}
          className="w-full"
        >
          {disabled ? t('register.creating') : t('register.createAccount')}
        </Button>
      </form>
    </AuthLayout>
  );
};
