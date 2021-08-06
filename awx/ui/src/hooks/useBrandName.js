import { useEffect, useState } from 'react';
import { RootAPI } from 'api';

export default function useBrandName() {
  const [brandName, setBrandName] = useState('');

  useEffect(() => {
    async function fetchBrandName() {
      const {
        data: { BRAND_NAME },
      } = await RootAPI.readAssetVariables();
      setBrandName(BRAND_NAME);
    }
    fetchBrandName();
  }, []);

  return brandName;
}
