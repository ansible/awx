import { useEffect } from 'react';
import { useLocation, useHistory } from 'react-router';
import { PERSISTENT_FILTER_KEY } from '../../constants';

export default function PersistentFilters({ pageKey, children }) {
  const location = useLocation();
  const history = useHistory();

  useEffect(() => {
    if (!location.search.includes('restoreFilters=true')) {
      return;
    }

    const filterString = sessionStorage.getItem(PERSISTENT_FILTER_KEY);
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
    sessionStorage.setItem(PERSISTENT_FILTER_KEY, JSON.stringify(filter));
  }, [location.search, pageKey]);

  return children;
}
