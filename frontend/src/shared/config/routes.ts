type Id = number | string;

export const routes = {
  login: '/login',
  home: '/',
  clubs: '/clubs',
  club: (clubId: Id) => `/clubs/${clubId}`,
  clubBlocks: (clubId: Id) => `/clubs/${clubId}/blocks`,
  clubSync: (clubId: Id) => `/clubs/${clubId}/sync`,
  clubReminders: (clubId: Id) => `/clubs/${clubId}/reminders`,
  clubSettings: (clubId: Id) => `/clubs/${clubId}/settings`,
  users: '/users',
  admins: '/admins',
  roles: '/roles',
  settings: '/settings',
} as const;
