import { createTheme } from '@mantine/core';
import { Day } from '@mantine/dates';

import classes from './theme.module.css';

export const theme = createTheme({
  primaryColor: 'indigo',
  defaultRadius: 'md',
  fontFamily: 'Inter, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif',
  components: {
    Day: Day.extend({ defaultProps: { highlightToday: true }, classNames: { day: classes.today } }),
  },
});
