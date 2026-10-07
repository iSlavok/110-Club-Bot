export const routes = {
  login: '/login',
  dashboard: '/',
  clubs: '/clubs',
  club: (clubId: number | string) => `/clubs/${clubId}`,
  users: '/users',
  admins: '/admins',
  roles: '/roles',
} as const;
