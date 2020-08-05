import React, { useCallback, useEffect } from 'react';
import { func, bool } from 'prop-types';
import { withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { InventoriesAPI } from '../../api';
import { Inventory } from '../../types';
import Lookup from './Lookup';
import OptionsList from '../OptionsList';
import useRequest from '../../util/useRequest';
import { getQSConfig, parseQueryString } from '../../util/qs';
import LookupErrorMessage from './shared/LookupErrorMessage';

const QS_CONFIG = getQSConfig('inventory', {
  page: 1,
  page_size: 5,
  order_by: 'name',
});

function InventoryLookup({ value, onChange, onBlur, required, i18n, history }) {
  const {
    result: { inventories, count, actions, relatedSearchFields },
    request: fetchInventories,
    error,
    isLoading,
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
    { inventories: [], count: 0, actions: {}, relatedSearchFields: [] }
  );

  useEffect(() => {
    fetchInventories();
  }, [fetchInventories]);

  const relatedSearchableKeys = relatedSearchFields || [];
  const searchableKeys = Object.keys(actions?.GET || {}).filter(
    key => actions.GET[key].filterable
  );

  return (
    <>
      <Lookup
        id="inventory-lookup"
        header={i18n._(t`Inventory`)}
        value={value}
        onChange={onChange}
        onBlur={onBlur}
        required={required}
        isLoading={isLoading}
        qsConfig={QS_CONFIG}
        renderOptionsList={({ state, dispatch, canDelete }) => (
          <OptionsList
            value={state.selectedItems}
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
            multiple={state.multiple}
            header={i18n._(t`Inventory`)}
            name="inventory"
            qsConfig={QS_CONFIG}
            readOnly={!canDelete}
            selectItem={item => dispatch({ type: 'SELECT_ITEM', item })}
            deselectItem={item => dispatch({ type: 'DESELECT_ITEM', item })}
          />
        )}
      />
      <LookupErrorMessage error={error} />
    </>
  );
}

InventoryLookup.propTypes = {
  value: Inventory,
  onChange: func.isRequired,
  required: bool,
};

InventoryLookup.defaultProps = {
  value: null,
  required: false,
};

export default withI18n()(withRouter(InventoryLookup));
