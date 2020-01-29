import { useEffect, useState, useRef, useCallback } from 'react';

// Initial approach (useEffect baked in)
export default function useEndpoint(fetch) {
  const [results, setResults] = useState([]);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const isMounted = useRef(null);

  useEffect(() => {
    isMounted.current = true;
    (async () => {
      // Do we want this set here or not? Can result in extra
      // unmounting/re-mounting of child components
      setIsLoading(true);
      try {
        const fetchedResults = await fetch();
        if (isMounted.current) {
          setResults(fetchedResults);
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
    })();
    return () => {
      isMounted.current = false;
    };
  }, [fetch]);

  return {
    results,
    isLoading,
    error,
  };
}

// more versatile approach (returns function to make API request)
export function useFetch(fetch, initialValue) {
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
    fetch: useCallback(async () => {
      setIsLoading(true);
      try {
        const response = await fetch();
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
    }, [fetch]),
  };
}
