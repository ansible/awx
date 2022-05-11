import { useEffect } from 'react';
import { useLocation, useHistory } from 'react-router';

const STORAGE_KEY = 'persistentFilter';

export default function PersistentFilters({ pageKey, children }) {
  const location = useLocation();
  const history = useHistory();

  useEffect(() => {
    if (!location.search.includes('restoreFilters=true')) {
      return;
    }

    const filterString = sessionStorage.getItem(STORAGE_KEY);
    const filter = filterString ? JSON.parse(filterString) : { qs: '' };

    if (filter.pageKey === pageKey) {
      history.replace(`${location.pathname}${filter.qs}`);
    } else {
      history.replace(location.pathname);
    }
  }, [history, location, pageKey]);

  useEffect(() => {
    const filter = {
      pageKey,
      qs: location.search,
    };
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(filter));
  }, [location.search, pageKey]);

  return children;
}
