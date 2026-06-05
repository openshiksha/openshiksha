import { useState } from 'react';
import { Link } from 'react-router-dom';
import type { AxiosError } from 'axios';
import { AuthLayout } from '@/features/auth/AuthLayout';
import { Button, EmptyState, Input, Textarea } from '@/shared/ui';
import { useEnquireMutation } from './useEnquireMutation';

function extractError(err: unknown): string {
  const axiosErr = err as AxiosError<{ details?: Record<string, string[]> }>;
  const details = axiosErr?.response?.data?.details;
  if (details) {
    const firstKey = Object.keys(details)[0];
    if (firstKey && Array.isArray(details[firstKey])) return details[firstKey][0];
  }
  return 'Something went wrong. Please try again.';
}

export const EnquirePage = () => {
  const mutation = useEnquireMutation();
  const [form, setForm] = useState({
    name: '',
    school: '',
    email: '',
    phone: '',
    message: '',
  });

  const set =
    (field: keyof typeof form) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
      setForm((prev) => ({ ...prev, [field]: e.target.value }));

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    mutation.mutate({
      name: form.name,
      school: form.school,
      email: form.email,
      phone: form.phone || undefined,
      message: form.message || undefined,
    });
  };

  if (mutation.isSuccess) {
    return (
      <AuthLayout
        title="Bring OpenShiksha to your school"
        subtitle="Tell us a little about your school and our team will reach out to set you up."
      >
        <EmptyState
          title="Thank you for your enquiry"
          description="Our team will be in touch shortly."
          action={
            <Link to="/login">
              <Button variant="ghost">← Back to sign in</Button>
            </Link>
          }
        />
      </AuthLayout>
    );
  }

  return (
    <AuthLayout
      title="Bring OpenShiksha to your school"
      subtitle="Tell us a little about your school and our team will reach out to set you up."
      footer={
        <p>
          Already with us?{' '}
          <Link to="/login" className="font-semibold text-brand-700 hover:text-brand-800">
            Sign in
          </Link>
        </p>
      }
    >
      <form onSubmit={handleSubmit} noValidate className="space-y-4">
        <Input
          label="Your name"
          id="name"
          value={form.name}
          onChange={set('name')}
          required
          disabled={mutation.isPending}
          autoComplete="name"
        />
        <Input
          label="School or organisation"
          id="school"
          value={form.school}
          onChange={set('school')}
          required
          disabled={mutation.isPending}
          autoComplete="organization"
        />
        <Input
          label="Email"
          id="email"
          type="email"
          value={form.email}
          onChange={set('email')}
          required
          disabled={mutation.isPending}
          autoComplete="email"
        />
        <Input
          label="Phone"
          hint="Optional"
          id="phone"
          value={form.phone}
          onChange={set('phone')}
          disabled={mutation.isPending}
          autoComplete="tel"
        />
        <Textarea
          label="Anything we should know?"
          hint="Optional"
          id="message"
          value={form.message}
          onChange={set('message')}
          disabled={mutation.isPending}
          rows={3}
        />

        {mutation.isError && (
          <div
            role="alert"
            className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700"
          >
            {extractError(mutation.error)}
          </div>
        )}

        <Button
          type="submit"
          variant="brand"
          size="lg"
          className="w-full"
          disabled={
            mutation.isPending || !form.name || !form.school || !form.email
          }
        >
          {mutation.isPending ? 'Sending…' : 'Send enquiry'}
        </Button>
      </form>
    </AuthLayout>
  );
};
