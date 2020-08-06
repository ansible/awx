import React, { useCallback, useEffect } from 'react';
import { useHistory } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { useField } from 'formik';
import { InventoriesAPI } from '../../../api';
import { getQSConfig, parseQueryString } from '../../../util/qs';
import useRequest from '../../../util/useRequest';
import OptionsList from '../../OptionsList';
import ContentLoading from '../../ContentLoading';
import ContentError from '../../ContentError';

const QS_CONFIG = getQSConfig('inventory', {
  page: 1,
  page_size: 5,
  order_by: 'name',
});

function InventoryStep({ i18n }) {
  const [field, , helpers] = useField({
    name: 'inventory',
  });
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
        ).map(val => val.slice(0, -8)),
        searchableKeys: Object.keys(
          actionsResponse.data.actions?.GET || {}
        ).filter(key => actionsResponse.data.actions?.GET[key].filterable),
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
    <OptionsList
      value={field.value ? [field.value] : []}
      options={inventories}
      optionCount={count}
      searchColumns={[
        {
          name: i18n._(t`Name`),
          key: 'name__icontains',
          isDefault: true,
        },
        {
          name: i18n._(t`Created By (Username)`),
          key: 'created_by__username__icontains',
        },
        {
          name: i18n._(t`Modified By (Username)`),
          key: 'modified_by__username__icontains',
        },
      ]}
      sortColumns={[
        {
          name: i18n._(t`Name`),
          key: 'name',
        },
      ]}
      searchableKeys={searchableKeys}
      relatedSearchableKeys={relatedSearchableKeys}
      header={i18n._(t`Inventory`)}
      name="inventory"
      qsConfig={QS_CONFIG}
      readOnly
      selectItem={helpers.setValue}
      deselectItem={() => field.onChange(null)}
    />
  );
}

export default withI18n()(InventoryStep);
