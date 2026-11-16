import { createTheme, Modal, ScrollArea } from '@mantine/core';
import { Day } from '@mantine/dates';

import classes from './theme.module.css';

export const theme = createTheme({
  primaryColor: 'indigo',
  defaultRadius: 'md',
  fontFamily: 'Inter, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif',
  components: {
    // A native scrollbar cuts the rounded right corners of a long modal.
    Modal: Modal.extend({ defaultProps: { scrollAreaComponent: ScrollArea.Autosize } }),
    Day: Day.extend({ defaultProps: { highlightToday: true }, classNames: { day: classes.today } }),
  },
});
