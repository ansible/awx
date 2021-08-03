import { useEffect, useRef } from 'react';
import { RootAPI } from 'api';

export default function useBrandName() {
  const platform = useRef({});

  useEffect(() => {
    async function fetchBrandName() {
      const {
        data: { BRAND_NAME, COMPONENT_NAME },
      } = await RootAPI.readAssetVariables();
      platform.current.brandName = BRAND_NAME;
      platform.current.componentName = COMPONENT_NAME || '';
    }
    fetchBrandName();
  }, []);

  return platform;
}
