import { useState } from 'react';
import { Link } from 'react-router-dom';
import type { AxiosError } from 'axios';
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

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-50 to-blue-100 py-12 px-4">
      <div className="w-full max-w-lg">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-indigo-600 rounded-2xl mb-4 shadow-lg">
            <span className="text-white text-2xl font-bold">OS</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Bring OpenShiksha to your school</h1>
          <p className="text-gray-500 mt-1 text-sm">
            Tell us about your school and our team will reach out to set you up.
          </p>
        </div>

        <div className="bg-white rounded-2xl shadow-xl p-8">
          {mutation.isSuccess ? (
            <div className="text-center py-6" role="status">
              <div className="inline-flex items-center justify-center w-12 h-12 bg-green-100 rounded-full mb-4">
                <span className="text-green-600 text-2xl">✓</span>
              </div>
              <h2 className="text-lg font-semibold text-gray-900">Thank you for your enquiry</h2>
              <p className="text-gray-500 mt-1 text-sm">
                Our team will be in touch with you shortly.
              </p>
              <Link
                to="/login"
                className="inline-block mt-6 text-indigo-600 hover:text-indigo-800 text-sm"
              >
                ← Back to sign in
              </Link>
            </div>
          ) : (
            <form onSubmit={handleSubmit} noValidate>
              <div className="space-y-4">
                <Field label="Your Name" id="name" value={form.name} onChange={set('name')} required disabled={mutation.isPending} />
                <Field label="School / Organization" id="school" value={form.school} onChange={set('school')} required disabled={mutation.isPending} />
                <Field label="Email" id="email" type="email" value={form.email} onChange={set('email')} required disabled={mutation.isPending} autoComplete="email" />
                <Field label="Phone (optional)" id="phone" value={form.phone} onChange={set('phone')} disabled={mutation.isPending} autoComplete="tel" />
                <div>
                  <label htmlFor="message" className="block text-sm font-medium text-gray-700 mb-1">
                    Message (optional)
                  </label>
                  <textarea
                    id="message"
                    value={form.message}
                    onChange={set('message')}
                    disabled={mutation.isPending}
                    rows={3}
                    className="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-gray-900 placeholder-gray-400 disabled:bg-gray-50"
                  />
                </div>

                {mutation.isError && (
                  <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700" role="alert">
                    {extractError(mutation.error)}
                  </div>
                )}

                <button
                  type="submit"
                  disabled={mutation.isPending || !form.name || !form.school || !form.email}
                  className="w-full py-2.5 px-4 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white font-semibold rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
                >
                  {mutation.isPending ? 'Sending…' : 'Send Enquiry'}
                </button>
              </div>
            </form>
          )}
        </div>

        <p className="text-center text-sm text-gray-500 mt-4">
          <Link to="/login" className="text-indigo-600 hover:text-indigo-800">
            ← Back to sign in
          </Link>
        </p>
      </div>
    </div>
  );
};

interface FieldProps {
  label: string;
  id: string;
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  type?: string;
  required?: boolean;
  disabled?: boolean;
  autoComplete?: string;
}

const Field = ({ label, id, value, onChange, type = 'text', required, disabled, autoComplete }: FieldProps) => (
  <div>
    <label htmlFor={id} className="block text-sm font-medium text-gray-700 mb-1">
      {label} {required && <span className="text-red-500">*</span>}
    </label>
    <input
      id={id}
      type={type}
      value={value}
      onChange={onChange}
      required={required}
      disabled={disabled}
      autoComplete={autoComplete}
      className="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-gray-900 placeholder-gray-400 disabled:bg-gray-50 disabled:text-gray-500"
    />
  </div>
);
