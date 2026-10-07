import { useState } from 'react';

export const PER_PAGE = 50;

export interface PageState {
  page: number;
  setPage: (page: number) => void;
  params: { page: number; per_page: number };
}

export function usePage(perPage = PER_PAGE): PageState {
  const [page, setPage] = useState(1);
  return { page, setPage, params: { page, per_page: perPage } };
}
