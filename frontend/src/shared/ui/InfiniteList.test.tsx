import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';

import { useListClubsInfinite, type ClubResponse } from '@/shared/api';
import { infinitePage, useInfinitePage } from '@/shared/lib/infinite-page';
import { pageOf } from '@/test/fixtures';
import { revealListEnds } from '@/test/intersection';
import { renderWithProviders } from '@/test/render';
import { server } from '@/test/server';

import { InfiniteList } from './InfiniteList';

function club(id: number): ClubResponse {
  return {
    id,
    title: `Клуб ${id}`,
    chat_id: null,
    reminders_topic_id: null,
    spreadsheet_id: null,
    sheet_name: null,
    is_active: true,
  };
}

function Clubs() {
  const query = useListClubsInfinite({ per_page: 2 }, infinitePage);
  const clubs = useInfinitePage(query);
  return (
    <InfiniteList list={clubs} filters={<span>Фильтры</span>} emptyText="Клубов нет">
      {(items) => (
        <ul>
          {items.map((item) => (
            <li key={item.id}>{item.title}</li>
          ))}
        </ul>
      )}
    </InfiniteList>
  );
}

describe('InfiniteList', () => {
  it('loads the next page when the end comes into view, until the last one', async () => {
    const requested: string[] = [];
    server.use(
      http.get('/api/v1/clubs', ({ request }) => {
        requested.push(new URL(request.url).searchParams.get('page') ?? '');
        return pageOf([1, 2, 3, 4, 5].map(club), request);
      }),
    );
    renderWithProviders(<Clubs />);

    expect(await screen.findByText('Клуб 2')).toBeInTheDocument();
    expect(screen.getByText('Фильтры')).toBeInTheDocument();
    expect(screen.queryByText('Клуб 3')).not.toBeInTheDocument();

    revealListEnds();
    expect(await screen.findByText('Клуб 4')).toBeInTheDocument();
    revealListEnds();
    expect(await screen.findByText('Клуб 5')).toBeInTheDocument();
    expect(screen.getByText('Всего: 5')).toBeInTheDocument();

    revealListEnds();
    expect(requested).toEqual(['1', '2', '3']);
  });

  it('shows the empty state', async () => {
    server.use(http.get('/api/v1/clubs', ({ request }) => pageOf([], request)));

    renderWithProviders(<Clubs />);

    expect(await screen.findByText('Клубов нет')).toBeInTheDocument();
  });

  it('shows why the first page failed', async () => {
    server.use(
      http.get('/api/v1/clubs', () =>
        HttpResponse.json({ code: 'PERMISSION_DENIED', message: 'denied' }, { status: 403 }),
      ),
    );

    renderWithProviders(<Clubs />);

    expect(await screen.findByText('Недостаточно прав.')).toBeInTheDocument();
  });

  it('keeps loaded rows and offers a retry when a next page fails', async () => {
    let failNextPage = true;
    server.use(
      http.get('/api/v1/clubs', ({ request }) => {
        const page = new URL(request.url).searchParams.get('page');
        if (page === '2' && failNextPage) {
          failNextPage = false;
          return HttpResponse.json({ code: 'INTERNAL_ERROR', message: 'boom' }, { status: 500 });
        }
        return pageOf([1, 2, 3].map(club), request);
      }),
    );
    renderWithProviders(<Clubs />);
    expect(await screen.findByText('Клуб 2')).toBeInTheDocument();

    revealListEnds();
    await userEvent.click(await screen.findByRole('button', { name: /Повторить/ }));

    expect(await screen.findByText('Клуб 3')).toBeInTheDocument();
    expect(screen.getByText('Клуб 1')).toBeInTheDocument();
  });
});
