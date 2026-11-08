import { Button } from '@mantine/core';
import { IconDownload } from '@tabler/icons-react';

interface DownloadButtonProps {
  href: string;
  label?: string;
}

// A plain link: the session cookie goes with it, and the browser saves the file under the server's name.
export function DownloadButton({ href, label = 'Скачать .xlsx' }: DownloadButtonProps) {
  return (
    <Button
      component="a"
      href={href}
      download
      variant="default"
      leftSection={<IconDownload size={16} />}
    >
      {label}
    </Button>
  );
}
