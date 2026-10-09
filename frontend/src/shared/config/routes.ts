type Id = number | string;

export const routes = {
  login: '/login',
  home: '/',
  clubs: '/clubs',
  club: (clubId: Id) => `/clubs/${clubId}`,
  clubBlocks: (clubId: Id) => `/clubs/${clubId}/blocks`,
  clubSettings: (clubId: Id) => `/clubs/${clubId}/settings`,
  users: '/users',
  admins: '/admins',
  roles: '/roles',
} as const;
