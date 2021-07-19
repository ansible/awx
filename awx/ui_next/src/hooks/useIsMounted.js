import { useEffect, useRef } from 'react';

export default function useIsMounted() {
  const isMounted = useRef(null);
  useEffect(() => {
    isMounted.current = true;
    return () => {
      isMounted.current = false;
    };
  });
  return isMounted;
}
