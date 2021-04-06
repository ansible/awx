import { useRef } from 'react';

export default function useDebounce(fn, delay) {
  const timeOutRef = useRef(null);

  function debouncedFunction(...args) {
    window.clearTimeout(timeOutRef.current);
    timeOutRef.current = window.setTimeout(() => {
      fn(...args);
    }, delay);
  }

  return debouncedFunction;
}
