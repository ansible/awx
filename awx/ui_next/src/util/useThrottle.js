import { useState, useEffect, useRef } from 'react';

export default function useThrottle(value, limit) {
  const [throttledValue, setThrottledValue] = useState(value);
  const lastRan = useRef(Date.now());
  const initialValue = useRef(value);

  useEffect(() => {
    if (value !== initialValue.current) {
      setThrottledValue(value);
      return () => {};
    }

    const handler = setTimeout(() => {
      if (Date.now() - lastRan.current >= limit) {
        lastRan.current = Date.now();
        setThrottledValue(value);
      }
    }, limit - (Date.now() - lastRan.current));

    return () => {
      clearTimeout(handler);
    };
  }, [value, limit]);

  return throttledValue;
}
