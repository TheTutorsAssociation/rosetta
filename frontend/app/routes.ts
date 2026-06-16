import { type RouteConfig, index, route } from '@react-router/dev/routes';

/**
 * Programmatic route manifest (React Router framework mode). `react-router
 * typegen` reads this to generate the per-route `+types/*` modules, so every
 * route declared here gets type-safe `Route.LoaderArgs` / `Route.ActionArgs` /
 * `Route.ComponentProps`.
 */
export default [
  index('routes/home.tsx'),

  route('login', 'routes/auth/login.tsx'),

  route('*', 'routes/not-found.tsx'),
] satisfies RouteConfig;
