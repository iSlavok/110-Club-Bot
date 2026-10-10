type Id = number | string;

export const routes = {
  login: '/login',
  home: '/',
  clubs: '/clubs',
  club: (clubId: Id) => `/clubs/${clubId}`,
  clubBlocks: (clubId: Id) => `/clubs/${clubId}/blocks`,
  clubSync: (clubId: Id) => `/clubs/${clubId}/sync`,
  clubLessons: (clubId: Id) => `/clubs/${clubId}/lessons`,
  clubLesson: (clubId: Id, lessonId: Id) => `/clubs/${clubId}/lessons/${lessonId}`,
  clubReminders: (clubId: Id) => `/clubs/${clubId}/reminders`,
  clubSettings: (clubId: Id) => `/clubs/${clubId}/settings`,
  users: '/users',
  admins: '/admins',
  roles: '/roles',
  settings: '/settings',
} as const;
