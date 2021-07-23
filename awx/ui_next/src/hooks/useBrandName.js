import { useEffect, useRef } from 'react';
import { RootAPI } from 'api';

export default function useBrandName() {
  const brandName = useRef('');

  useEffect(() => {
    async function fetchBrandName() {
      const {
        data: { BRAND_NAME },
      } = await RootAPI.readAssetVariables();

      brandName.current = BRAND_NAME;
    }
    fetchBrandName();
  }, []);

  return brandName;
}
