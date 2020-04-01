import React, { useCallback, useEffect } from 'react';
import { useHistory } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { useField } from 'formik';
import { InventoriesAPI } from '@api';
import { getQSConfig, parseQueryString } from '@util/qs';
import useRequest from '@util/useRequest';
import OptionsList from '@components/OptionsList';
import ContentLoading from '@components/ContentLoading';

const QS_CONFIG = getQSConfig('inventory', {
  page: 1,
  page_size: 5,
  order_by: 'name',
});

function InventoryStep({ i18n }) {
  const history = useHistory();
  const [field, , helpers] = useField('inventory');

  const {
    isLoading,
    // error,
    result: { inventories, count },
    request: fetchInventories,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, history.location.search);
      const { data } = await InventoriesAPI.read(params);
      return {
        inventories: data.results,
        count: data.count,
      };
    }, [history.location]),
    {
      count: 0,
      inventories: [],
    }
  );

  useEffect(() => {
    fetchInventories();
  }, [fetchInventories]);

  if (isLoading) {
    return <ContentLoading />;
  }

  return (
    <OptionsList
      value={field.value ? [field.value] : []}
      options={inventories}
      optionCount={count}
      searchColumns={[
        {
          name: i18n._(t`Name`),
          key: 'name',
          isDefault: true,
        },
        {
          name: i18n._(t`Created By (Username)`),
          key: 'created_by__username',
        },
        {
          name: i18n._(t`Modified By (Username)`),
          key: 'modified_by__username',
        },
      ]}
      sortColumns={[
        {
          name: i18n._(t`Name`),
          key: 'name',
        },
      ]}
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
