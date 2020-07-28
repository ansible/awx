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
import { required } from '../../../util/validators';

const QS_CONFIG = getQSConfig('inventory', {
  page: 1,
  page_size: 5,
  order_by: 'name',
});

function InventoryStep({ i18n }) {
  const [field, , helpers] = useField({
    name: 'inventory',
    validate: required(null, i18n),
  });
  const history = useHistory();

  const {
    isLoading,
    error,
    result: { inventories, count, actions, relatedSearchFields },
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
        actions: actionsResponse.data.actions,
        relatedSearchFields: (
          actionsResponse?.data?.related_search_fields || []
        ).map(val => val.slice(0, -8)),
      };
    }, [history.location]),
    {
      count: 0,
      inventories: [],
      actions: {},
      relatedSearchFields: [],
    }
  );

  useEffect(() => {
    fetchInventories();
  }, [fetchInventories]);

  const relatedSearchableKeys = relatedSearchFields || [];
  const searchableKeys = Object.keys(actions?.GET || {}).filter(
    key => actions.GET[key].filterable
  );

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
      toolbarSearchableKeys={searchableKeys}
      toolbarRelatedSearchableKeys={relatedSearchableKeys}
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
