import { useEffect } from 'react';
import useBrandName from './useBrandName';

export default function useTitle(title) {
  const brandName = useBrandName();

  useEffect(() => {
    const prevTitle = document.title;
    if (title) {
      document.title = `${brandName} | ${title}`;
    } else {
      document.title = brandName;
    }

    return () => {
      document.title = prevTitle;
    };
  }, [title, brandName]);
}
