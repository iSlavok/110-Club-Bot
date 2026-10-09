import { Paper } from '@mantine/core';

import { usePermission } from '@/entities/session';
import { VkLinkModeForm } from '@/features/settings';
import { useGetSettings } from '@/shared/api';
import { PageHeader } from '@/shared/ui/PageHeader';
import { QueryState } from '@/shared/ui/QueryState';

export function SettingsPage() {
  const settings = useGetSettings();
  const canEdit = usePermission('settings.edit');

  return (
    <>
      <PageHeader title="Настройки бота" />
      <QueryState data={settings.data} error={settings.error} isPending={settings.isPending}>
        {(data) => (
          <Paper withBorder radius="md" p="lg" maw={720}>
            <VkLinkModeForm key={data.updated_at} settings={data} canEdit={canEdit} />
          </Paper>
        )}
      </QueryState>
    </>
  );
}
