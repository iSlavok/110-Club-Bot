import { Image } from '@mantine/core';

import logo from '@/shared/assets/logo.png';

// Always shown next to the club name, so screen readers skip it.
export function Logo({ size }: { size: number }) {
  return <Image src={logo} alt="" w={size} h={size} radius="sm" />;
}
