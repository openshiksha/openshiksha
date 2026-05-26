import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useRegisterSchoolMutation } from './useRegisterMutation';
import type { AxiosError } from 'axios';

function extractError(err: unknown): string {
  const axiosErr = err as AxiosError<Record<string, string[]>>;
  const data = axiosErr?.response?.data;
  if (!data) return 'Registration failed. Please try again.';
  const firstKey = Object.keys(data)[0];
  if (firstKey && Array.isArray(data[firstKey])) return data[firstKey][0];
  return 'Registration failed. Please try again.';
}

export const RegisterSchoolPage = () => {
  const mutation = useRegisterSchoolMutation();
  const [form, setForm] = useState({
    first_name: '',
    last_name: '',
    username: '',
    password: '',
    email: '',
    join_code: '',
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

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 py-12 px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-indigo-600 rounded-2xl mb-4 shadow-lg">
            <span className="text-white text-2xl font-bold">OS</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Join Your School</h1>
          <p className="text-gray-500 mt-1 text-sm">Enter the join code from your teacher</p>
        </div>

        <div className="bg-white rounded-2xl shadow-xl p-8">
          <form onSubmit={handleSubmit} noValidate>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <FormField label="First Name" id="first_name" value={form.first_name} onChange={set('first_name')} disabled={mutation.isPending} />
                <FormField label="Last Name" id="last_name" value={form.last_name} onChange={set('last_name')} disabled={mutation.isPending} />
              </div>

              <FormField label="Username" id="username" value={form.username} onChange={set('username')} required disabled={mutation.isPending} autoComplete="username" />
              <FormField label="Password" id="password" type="password" value={form.password} onChange={set('password')} required disabled={mutation.isPending} autoComplete="new-password" />
              <FormField label="Email (optional)" id="email" type="email" value={form.email} onChange={set('email')} disabled={mutation.isPending} autoComplete="email" />

              <div>
                <label htmlFor="join_code" className="block text-sm font-medium text-gray-700 mb-1">
                  Classroom Join Code <span className="text-red-500">*</span>
                </label>
                <input
                  id="join_code"
                  type="text"
                  required
                  value={form.join_code}
                  onChange={set('join_code')}
                  disabled={mutation.isPending}
                  placeholder="e.g. ABC123"
                  className="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-gray-900 uppercase tracking-widest font-mono placeholder-gray-400 placeholder:normal-case placeholder:tracking-normal placeholder:font-sans"
                  maxLength={8}
                />
              </div>

              {mutation.isError && (
                <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700" role="alert">
                  {extractError(mutation.error)}
                </div>
              )}

              <button
                type="submit"
                disabled={mutation.isPending || !form.username || !form.password || !form.join_code}
                className="w-full py-2.5 px-4 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white font-semibold rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
              >
                {mutation.isPending ? 'Creating account…' : 'Create Account'}
              </button>
            </div>
          </form>
        </div>

        <p className="text-center text-sm text-gray-500 mt-4">
          <Link to="/register" className="text-indigo-600 hover:text-indigo-800">
            ← Back
          </Link>
          {' · '}
          <Link to="/login" className="text-indigo-600 hover:text-indigo-800">
            Sign in
          </Link>
        </p>
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
  required?: boolean;
  disabled?: boolean;
  autoComplete?: string;
  placeholder?: string;
}

const FormField = ({ label, id, value, onChange, type = 'text', required, disabled, autoComplete, placeholder }: FormFieldProps) => (
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
      placeholder={placeholder}
      className="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-gray-900 placeholder-gray-400 disabled:bg-gray-50 disabled:text-gray-500"
    />
  </div>
);
