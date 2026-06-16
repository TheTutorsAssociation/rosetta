/**
 * Minimal, stable types shared across the app. Keep this module free of
 * feature-specific shapes — those belong in their own type modules. Field
 * casing mirrors the backend by convention.
 */

export interface User {
  id: number;
  name: string;
  email?: string;
}
