import React, { useCallback, useEffect } from 'react';
import { func, bool, string } from 'prop-types';
import { withRouter } from 'react-router-dom';
import { t } from '@lingui/macro';
import { InventoriesAPI } from 'api';
import { Inventory } from 'types';
import useRequest from 'hooks/useRequest';
import { getQSConfig, parseQueryString, mergeParams } from 'util/qs';
import Lookup from './Lookup';
import OptionsList from '../OptionsList';
import LookupErrorMessage from './shared/LookupErrorMessage';
import FieldWithPrompt from '../FieldWithPrompt';

const QS_CONFIG = getQSConfig('inventory', {
  page: 1,
  page_size: 5,
  order_by: 'name',
  role_level: 'use_role',
});

function InventoryLookup({
  value,
  onChange,
  onBlur,
  history,
  required,
  isPromptableField,
  fieldId,
  promptId,
  promptName,
  isOverrideDisabled,
  validate,
  fieldName,
  isDisabled,
  hideSmartInventories,
}) {
  const {
    result: {
      inventories,
      count,
      relatedSearchableKeys,
      searchableKeys,
      canEdit,
    },
    request: fetchInventories,
    error,
    isLoading,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, history.location.search);
      const inventoryKindParams = hideSmartInventories
        ? { not__kind: 'smart' }
        : {};
      const [{ data }, actionsResponse] = await Promise.all([
        InventoriesAPI.read(
          mergeParams(params, {
            ...inventoryKindParams,
          })
        ),
        InventoriesAPI.readOptions(),
      ]);

      return {
        inventories: data.results,
        count: data.count,
        relatedSearchableKeys: (
          actionsResponse?.data?.related_search_fields || []
        ).map((val) => val.slice(0, -8)),
        searchableKeys: Object.keys(
          actionsResponse.data.actions?.GET || {}
        ).filter((key) => {
          if (['kind', 'host_filter'].includes(key) && hideSmartInventories) {
            return false;
          }
          return actionsResponse.data.actions?.GET[key].filterable;
        }),
        canEdit:
          Boolean(actionsResponse.data.actions.POST) || isOverrideDisabled,
      };
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [history.location]),
    {
      inventories: [],
      count: 0,
      relatedSearchableKeys: [],
      searchableKeys: [],
      canEdit: false,
    }
  );

  const checkInventoryName = useCallback(
    async (name) => {
      if (!name) {
        onChange(null);
        return;
      }

      try {
        const {
          data: { results: nameMatchResults, count: nameMatchCount },
        } = await InventoriesAPI.read({ name });
        onChange(nameMatchCount ? nameMatchResults[0] : null);
      } catch {
        onChange(null);
      }
    },
    [onChange]
  );

  useEffect(() => {
    fetchInventories();
  }, [fetchInventories]);

  return isPromptableField ? (
    <>
      <FieldWithPrompt
        fieldId={fieldId}
        isRequired={required}
        label={t`Inventory`}
        promptId={promptId}
        promptName={promptName}
        isDisabled={!canEdit || isDisabled}
        tooltip={t`Select the inventory containing the hosts
            you want this job to manage.`}
      >
        <Lookup
          id="inventory-lookup"
          header={t`Inventory`}
          value={value}
          onChange={onChange}
          onBlur={onBlur}
          required={required}
          onDebounce={checkInventoryName}
          fieldName={fieldName}
          validate={validate}
          isLoading={isLoading}
          isDisabled={!canEdit || isDisabled}
          qsConfig={QS_CONFIG}
          renderOptionsList={({ state, dispatch, canDelete }) => (
            <OptionsList
              value={state.selectedItems}
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
              multiple={state.multiple}
              header={t`Inventory`}
              name="inventory"
              qsConfig={QS_CONFIG}
              readOnly={!canDelete}
              selectItem={(item) => dispatch({ type: 'SELECT_ITEM', item })}
              deselectItem={(item) => dispatch({ type: 'DESELECT_ITEM', item })}
            />
          )}
        />
        <LookupErrorMessage error={error} />
      </FieldWithPrompt>
    </>
  ) : (
    <>
      <Lookup
        id="inventory-lookup"
        header={t`Inventory`}
        value={value}
        onChange={onChange}
        onDebounce={checkInventoryName}
        fieldName={fieldName}
        validate={validate}
        onBlur={onBlur}
        required={required}
        isLoading={isLoading}
        isDisabled={!canEdit || isDisabled}
        qsConfig={QS_CONFIG}
        renderOptionsList={({ state, dispatch, canDelete }) => (
          <OptionsList
            value={state.selectedItems}
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
            multiple={state.multiple}
            header={t`Inventory`}
            name="inventory"
            qsConfig={QS_CONFIG}
            readOnly={!canDelete}
            selectItem={(item) => dispatch({ type: 'SELECT_ITEM', item })}
            deselectItem={(item) => dispatch({ type: 'DESELECT_ITEM', item })}
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
  isOverrideDisabled: bool,
  validate: func,
  fieldName: string,
  isDisabled: bool,
  hideSmartInventories: bool,
};

InventoryLookup.defaultProps = {
  value: null,
  required: false,
  isOverrideDisabled: false,
  validate: () => {},
  fieldName: 'inventory',
  isDisabled: false,
  hideSmartInventories: false,
};

export default withRouter(InventoryLookup);
