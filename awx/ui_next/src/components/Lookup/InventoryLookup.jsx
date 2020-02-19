import React, { useState, useEffect } from 'react';
import { func, bool } from 'prop-types';
import { withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { InventoriesAPI } from '@api';
import { Inventory } from '@types';
import Lookup from '@components/Lookup';
import { getQSConfig, parseQueryString } from '@util/qs';
import OptionsList from './shared/OptionsList';
import LookupErrorMessage from './shared/LookupErrorMessage';

const QS_CONFIG = getQSConfig('inventory', {
  page: 1,
  page_size: 5,
  order_by: 'name',
});

function InventoryLookup({ value, onChange, onBlur, required, i18n, history }) {
  const [inventories, setInventories] = useState([]);
  const [count, setCount] = useState(0);
  const [error, setError] = useState(null);

  useEffect(() => {
    (async () => {
      const params = parseQueryString(QS_CONFIG, history.location.search);
      try {
        const { data } = await InventoriesAPI.read(params);
        setInventories(data.results);
        setCount(data.count);
      } catch (err) {
        setError(err);
      }
    })();
  }, [history.location]);

  return (
    <>
      <Lookup
        id="inventory-lookup"
        header={i18n._(t`Inventory`)}
        value={value}
        onChange={onChange}
        onBlur={onBlur}
        required={required}
        qsConfig={QS_CONFIG}
        renderOptionsList={({ state, dispatch, canDelete }) => (
          <OptionsList
            value={state.selectedItems}
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
