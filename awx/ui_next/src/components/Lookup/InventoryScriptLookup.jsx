import React, { useCallback, useEffect } from 'react';
import { withRouter } from 'react-router-dom';
import { func, bool, number, node, string, oneOfType } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import { FormGroup } from '@patternfly/react-core';
import Lookup from './Lookup';
import LookupErrorMessage from './shared/LookupErrorMessage';
import OptionsList from '../OptionsList';
import { InventoriesAPI, InventoryScriptsAPI } from '../../api';
import { InventoryScript } from '../../types';
import useRequest from '../../util/useRequest';
import { getQSConfig, parseQueryString, mergeParams } from '../../util/qs';

const QS_CONFIG = getQSConfig('inventory_scripts', {
  order_by: 'name',
  page: 1,
  page_size: 5,
  role_level: 'admin_role',
});

function InventoryScriptLookup({
  helperTextInvalid,
  history,
  i18n,
  inventoryId,
  isValid,
  onBlur,
  onChange,
  required,
  value,
}) {
  const {
    result: { count, inventoryScripts, actions, relatedSearchFields },
    error,
    request: fetchInventoryScripts,
  } = useRequest(
    useCallback(async () => {
      const parsedParams = parseQueryString(QS_CONFIG, history.location.search);
      const [
        {
          data: { organization },
        },
        actionsResponse,
      ] = await Promise.all([
        InventoriesAPI.readDetail(inventoryId),
        InventoriesAPI.readOptions(),
      ]);
      const { data } = await InventoryScriptsAPI.read(
        mergeParams(parsedParams, { organization })
      );
      return {
        count: data.count,
        inventoryScripts: data.results,
        actions: actionsResponse.data.actions,
        relatedSearchFields: (
          actionsResponse?.data?.related_search_fields || []
        ).map(val => val.slice(0, -8)),
      };
    }, [history.location.search, inventoryId]),
    {
      count: 0,
      inventoryScripts: [],
      actions: {},
      relatedSearchFields: [],
    }
  );

  useEffect(() => {
    fetchInventoryScripts();
  }, [fetchInventoryScripts]);

  const relatedSearchableKeys = relatedSearchFields || [];
  const searchableKeys = Object.keys(actions?.GET || {}).filter(
    key => actions.GET[key].filterable
  );

  return (
    <FormGroup
      fieldId="inventory-script"
      helperTextInvalid={helperTextInvalid}
      isRequired={required}
      validated={isValid ? 'default' : 'error'}
      label={i18n._(t`Inventory script`)}
    >
      <Lookup
        id="inventory-script-lookup"
        header={i18n._(t`Inventory script`)}
        value={value}
        onChange={onChange}
        onBlur={onBlur}
        required={required}
        qsConfig={QS_CONFIG}
        renderOptionsList={({ state, dispatch, canDelete }) => (
          <OptionsList
            header={i18n._(t`Inventory script`)}
            multiple={state.multiple}
            name="inventory-script"
            optionCount={count}
            options={inventoryScripts}
            qsConfig={QS_CONFIG}
            readOnly={!canDelete}
            deselectItem={item => dispatch({ type: 'DESELECT_ITEM', item })}
            selectItem={item => dispatch({ type: 'SELECT_ITEM', item })}
            value={state.selectedItems}
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
          />
        )}
      />
      <LookupErrorMessage error={error} />
    </FormGroup>
  );
}

InventoryScriptLookup.propTypes = {
  helperTextInvalid: node,
  inventoryId: oneOfType([number, string]).isRequired,
  isValid: bool,
  onBlur: func,
  onChange: func.isRequired,
  required: bool,
  value: InventoryScript,
};

InventoryScriptLookup.defaultProps = {
  helperTextInvalid: '',
  isValid: true,
  onBlur: () => {},
  required: false,
  value: null,
};

export default withI18n()(withRouter(InventoryScriptLookup));
