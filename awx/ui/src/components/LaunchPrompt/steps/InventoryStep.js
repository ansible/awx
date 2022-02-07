import React, { useCallback, useEffect } from 'react';
import { useHistory } from 'react-router-dom';

import { t } from '@lingui/macro';
import { useField } from 'formik';
import styled from 'styled-components';
import { Alert } from '@patternfly/react-core';
import { InventoriesAPI } from 'api';
import { getSearchableKeys } from 'components/PaginatedTable';
import { getQSConfig, parseQueryString } from 'util/qs';
import useRequest from 'hooks/useRequest';
import OptionsList from '../../OptionsList';
import ContentLoading from '../../ContentLoading';
import ContentError from '../../ContentError';

const InventoryErrorAlert = styled(Alert)`
  margin-bottom: 20px;
`;

const QS_CONFIG = getQSConfig('inventory', {
  page: 1,
  page_size: 5,
  order_by: 'name',
  role_level: 'use_role',
});

function InventoryStep({ warningMessage = null }) {
  const [field, meta, helpers] = useField('inventory');

  const history = useHistory();

  const {
    isLoading,
    error,
    result: { inventories, count, relatedSearchableKeys, searchableKeys },
    request: fetchInventories,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, history.location.search);
      const [{ data }, actionsResponse] = await Promise.all([
        InventoriesAPI.read(params),
        InventoriesAPI.readOptions(),
      ]);
      return {
        inventories: data.results,
        count: data.count,
        relatedSearchableKeys: (
          actionsResponse?.data?.related_search_fields || []
        ).map((val) => val.slice(0, -8)),
        searchableKeys: getSearchableKeys(actionsResponse.data.actions?.GET),
      };
    }, [history.location]),
    {
      count: 0,
      inventories: [],
      relatedSearchableKeys: [],
      searchableKeys: [],
    }
  );

  useEffect(() => {
    fetchInventories();
  }, [fetchInventories]);

  if (isLoading) {
    return <ContentLoading />;
  }
  if (error) {
    return <ContentError error={error} />;
  }

  return (
    <>
      {meta.touched && meta.error && (
        <InventoryErrorAlert variant="danger" isInline title={meta.error} />
      )}
      {warningMessage}
      <OptionsList
        value={field.value ? [field.value] : []}
        options={inventories}
        optionCount={count}
        searchColumns={[
          {
            name: t`Name`,
            key: 'name__icontains',
            isDefault: true,
          },
          {
            name: t`Created By (Username)`,
            key: 'created_by__username__icontains',
          },
          {
            name: t`Modified By (Username)`,
            key: 'modified_by__username__icontains',
          },
        ]}
        sortColumns={[
          {
            name: t`Name`,
            key: 'name',
          },
        ]}
        searchableKeys={searchableKeys}
        relatedSearchableKeys={relatedSearchableKeys}
        header={t`Inventory`}
        name="inventory"
        qsConfig={QS_CONFIG}
        readOnly
        selectItem={helpers.setValue}
        deselectItem={() => field.onChange(null)}
      />
    </>
  );
}

export default InventoryStep;
