import { ReminderFeed } from '@/features/reminder';
import { useClubId } from '@/shared/lib/club-id';
import { PageHeader } from '@/shared/ui/PageHeader';

export function ClubRemindersPage() {
  const clubId = useClubId();
  return (
    <>
      <PageHeader title="Напоминания" />
      <ReminderFeed clubId={clubId} />
    </>
  );
}
