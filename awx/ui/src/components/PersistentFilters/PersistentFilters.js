import { useEffect } from 'react';
import { useLocation } from 'react-router';
import { PERSISTENT_FILTER_KEY } from '../../constants';

export default function PersistentFilters({ pageKey, children }) {
  const location = useLocation();

  useEffect(() => {
    const filter = {
      pageKey,
      qs: location.search,
    };
    sessionStorage.setItem(PERSISTENT_FILTER_KEY, JSON.stringify(filter));
  }, [location.search, pageKey]);

  return children;
}

export function getPersistentFilters(key) {
  const filterString = sessionStorage.getItem(PERSISTENT_FILTER_KEY);
  const filter = filterString ? JSON.parse(filterString) : { qs: '' };

  if (filter.pageKey === key) {
    return filter.qs;
  }
  return '';
}
