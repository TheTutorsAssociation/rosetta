/**
 * Single import surface for the UI primitives:
 *   import { Button, Heading, Input } from '~/components/ui';
 *
 * Prefer composing these primitives before writing new ones.
 */

export { Button } from './Button';
export type { ButtonProps, ButtonVariant, ButtonSize } from './Button';

export { Input } from './Input';
export type { InputProps } from './Input';

export { Heading } from './Heading';
export type { HeadingProps } from './Heading';

export { Alert } from './Alert';
export type { AlertProps, AlertVariant } from './Alert';

export { ErrorState } from './ErrorState';
export type { ErrorStateProps } from './ErrorState';
