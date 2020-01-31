import { useEffect, useState, useRef, useCallback } from 'react';

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
