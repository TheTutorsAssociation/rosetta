import type { Route } from './+types/signup';
import { Eye, EyeOff } from 'lucide-react';
import { useState } from 'react';
import type { ChangeEventHandler } from 'react';
import { Form, Link, redirect, useActionData, useNavigation } from 'react-router';
import { AuthFormLayout } from '~/components/auth/AuthFormLayout';
import { Alert, Button, Input } from '~/components/ui';
import { ApiError, authApi } from '~/data/api';
import { cn } from '~/helpers/cn';
import { buildMetaData } from '~/helpers/meta';

export function meta(): Route.MetaDescriptors {
  return buildMetaData('Sign up');
}

type ActionResult = { error: string };
type FieldName = 'firstName' | 'lastName' | 'email' | 'password' | 'confirmPassword';
type FieldErrors = Partial<Record<FieldName, string>>;

const MIN_PASSWORD_LENGTH = 8;
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function validateSignupFields({
  firstName,
  lastName,
  email,
  password,
  confirmPassword,
}: {
  firstName: string;
  lastName: string;
  email: string;
  password: string;
  confirmPassword: string;
}): FieldErrors {
  const errors: FieldErrors = {};

  if(!firstName) {
    errors.firstName = 'Enter your first name.';
  }

  if (!lastName) {
    errors.lastName = 'Enter your last name.';
  }
  if (!email) {
    errors.email = 'Enter your email.';
  } else if (!EMAIL_PATTERN.test(email)) {
    errors.email = 'Enter a valid email address.';
  }
  if (!password) {
    errors.password = 'Enter a password.';
  } else if (password.length < MIN_PASSWORD_LENGTH) {
    errors.password = 'Use a password with at least 8 characters.';
  }
  if (!confirmPassword) {
    errors.confirmPassword = 'Confirm your password.';
  } else if (password && confirmPassword !== password) {
    errors.confirmPassword = 'Passwords must match.';
  }

  return errors;
}

interface PasswordFieldProps {
  name: string;
  label: string;
  value: string;
  error?: string;
  visible: boolean;
  onChange: ChangeEventHandler<HTMLInputElement>;
  onToggle: () => void;
}

function PasswordField({
  name,
  label,
  value,
  error,
  visible,
  onChange,
  onToggle,
}: PasswordFieldProps) {
  const errorId = `${name}-error`;

  return (
    <div>
      <label htmlFor={name} className="mb-1 block text-small font-medium text-neutral-700">
        {label}
        <span className="ml-0.5 text-error">*</span>
      </label>
      <div className="relative">
        <input
          id={name}
          name={name}
          type={visible ? 'text' : 'password'}
          value={value}
          onChange={onChange}
          required
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? errorId : undefined}
          className={cn(
            'w-full rounded-xl border border-neutral-200 bg-white py-2 pl-3 pr-10 text-body outline-none transition focus:border-primary',
            error && 'border-error focus:border-error',
          )}
        />
        <button
          type="button"
          aria-label={visible ? `Hide ${label.toLowerCase()}` : `Show ${label.toLowerCase()}`}
          className="absolute right-2 top-1/2 inline-flex -translate-y-1/2 rounded-full p-1 text-neutral-500 transition hover:bg-neutral-100 hover:text-primary focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/50"
          onClick={onToggle}
        >
          {visible ? <EyeOff aria-hidden size={18} /> : <Eye aria-hidden size={18} />}
        </button>
      </div>
      {error && (
        <p id={errorId} className="mt-1 text-small text-error">
          {error}
        </p>
      )}
    </div>
  );
}

export async function clientAction({
  request,
}: Route.ClientActionArgs): Promise<Response | ActionResult> {
  const formData = await request.formData();
  const firstName = String(formData.get('first_name') ?? '');
  const lastName = String(formData.get('last_name') ?? '');
  const email = String(formData.get('email') ?? '');
  const phone = String(formData.get('phone') ?? '');
  const password = String(formData.get('password') ?? '');
  const confirmPassword = String(formData.get('confirm_password') ?? '');

  if (Object.keys(validateSignupFields({firstName, lastName, email, password, confirmPassword })).length) {
    return { error: 'Check the highlighted fields and try again.' };
  }


  try {
    await authApi.signup({
      first_name: firstName,
      last_name: lastName,
      email,
      ...(phone ? { phone } : {}),
      password,
    });
    return redirect('/login?signup=success');
  } catch (error) {
    if (error instanceof ApiError) {
      return {
        error: error.status === 409 ? 'An account with this email already exists.' : error.message,
      };
    }
    throw error;
  }
}

export default function Signup() {
  const actionData = useActionData<ActionResult>();
  const navigation = useNavigation();
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [passwordVisible, setPasswordVisible] = useState(false);
  const [confirmPasswordVisible, setConfirmPasswordVisible] = useState(false);

  const isSubmitting = navigation.state === 'submitting';

  const clearFieldError = (field: FieldName): void => {
    setFieldErrors((current) => {
      if (!current[field]) {
        return current;
      }
      const next = { ...current };
      delete next[field];
      return next;
    });
  };

  return (
    <AuthFormLayout
      title="Create your account"
      intro="Join The Tutors' Association member hub."
    >
      <Form
        method="post"
        className="space-y-5"
        noValidate
        onSubmit={(event) => {
          const errors = validateSignupFields({ firstName, lastName, email, password, confirmPassword });
          setFieldErrors(errors);
          if (Object.keys(errors).length) {
            event.preventDefault();
          }
        }}
      >
        {actionData?.error && <Alert variant="danger">{actionData.error}</Alert>}

        <div className="grid gap-4 sm:grid-cols-2">
          <Input
            name="first_name"
            label="First name"
            value={firstName}
            error={fieldErrors.firstName}
            required
            onChange={(event) => {
              setFirstName(event.target.value)
              clearFieldError('firstName');
            }}
          />

          <Input
            name="last_name"
            label="Last name"
            required
            error={fieldErrors.lastName}
            value={lastName}
            onChange={(event) => {
              setLastName(event.target.value);
              clearFieldError('lastName');
            }}
          />
        </div>

        <Input
          name="email"
          type="email"
          label="Email"
          required
          error={fieldErrors.email}
          value={email}
          onChange={(event) => {
            setEmail(event.target.value);
            clearFieldError('email');
          }}
        />

        <Input
          name="phone"
          type="tel"
          label="Phone"
          value={phone}
          onChange={(event) => setPhone(event.target.value)}
        />

        <PasswordField
          name="password"
          label="Password"
          error={fieldErrors.password}
          value={password}
          visible={passwordVisible}
          onToggle={() => setPasswordVisible((current) => !current)}
          onChange={(event) => {
            setPassword(event.target.value);
            clearFieldError('password');
          }}
        />

        <PasswordField
          name="confirm_password"
          label="Confirm password"
          error={fieldErrors.confirmPassword}
          value={confirmPassword}
          visible={confirmPasswordVisible}
          onToggle={() => setConfirmPasswordVisible((current) => !current)}
          onChange={(event) => {
            setConfirmPassword(event.target.value);
            clearFieldError('confirmPassword');
          }}
        />

        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Creating account...' : 'Create account'}
        </Button>

        <p className="text-body text-neutral-700">
          Already have an account?{' '}
          <Link to="/login" className="font-medium text-primary hover:underline">
            Sign in
          </Link>
          .
        </p>
      </Form>
    </AuthFormLayout>
  );
}
