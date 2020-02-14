import { useEffect, useState, useRef, useCallback } from 'react';
import { useLocation, useHistory } from 'react-router-dom';
import {
  parseQueryString,
  replaceParams,
  encodeNonDefaultQueryString,
} from './qs';

/*
 * The useRequest hook accepts a request function and returns an object with
 * four values:
 *   request: a function to call to invoke the request
 *   result: the value returned from the request function (once invoked)
 *   isLoading: boolean state indicating whether the request is in active/in flight
 *   error: any caught error resulting from the request
 *
 * The hook also accepts an optional second parameter which is a default
 * value to set as result before the first time the request is made.
 */
export default function useRequest(makeRequest, initialValue) {
  const [result, setResult] = useState(initialValue);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const isMounted = useRef(null);

  useEffect(() => {
    isMounted.current = true;
    return () => {
      isMounted.current = false;
    };
  }, []);

  return {
    result,
    error,
    isLoading,
    request: useCallback(async () => {
      setIsLoading(true);
      try {
        const response = await makeRequest();
        if (isMounted.current) {
          setResult(response);
        }
      } catch (err) {
        if (isMounted.current) {
          setError(err);
        }
      } finally {
        if (isMounted.current) {
          setIsLoading(false);
        }
      }
    }, [makeRequest]),
  };
}

export function useDeleteItems(
  makeRequest,
  { qsConfig, items, selected, fetchItems }
) {
  const location = useLocation();
  const history = useHistory();
  const [showError, setShowError] = useState(false);

  const { error, isLoading, request } = useRequest(makeRequest, null);

  const deleteItems = async () => {
    await request();
    const params = parseQueryString(qsConfig, location.search);
    if (params.page > 1 && selected.length === items.length) {
      const newParams = encodeNonDefaultQueryString(
        qsConfig,
        replaceParams(params, { page: params.page - 1 })
      );
      history.push(`${location.pathname}?${newParams}`);
    } else {
      fetchItems();
    }
  };

  return {
    isLoading,
    deleteItems,
    deletionError: showError && error,
    clearDeletionError: () => setShowError(false),
  };
}
