import 'styled-components/macro';
import React, { useState, useCallback, useEffect } from 'react';
import { withRouter } from 'react-router-dom';
import PropTypes from 'prop-types';
import { t } from '@lingui/macro';
import { ToolbarItem, Alert } from '@patternfly/react-core';
import { CredentialsAPI, CredentialTypesAPI } from 'api';
import { getSearchableKeys } from 'components/PaginatedTable';
import useRequest from 'hooks/useRequest';
import { getQSConfig, parseQueryString } from 'util/qs';
import useIsMounted from 'hooks/useIsMounted';
import AnsibleSelect from '../AnsibleSelect';
import CredentialChip from '../CredentialChip';
import OptionsList from '../OptionsList';
import Lookup from './Lookup';

const QS_CONFIG = getQSConfig('credentials', {
  page: 1,
  page_size: 5,
  order_by: 'name',
});

async function loadCredentials(params, selectedCredentialTypeId) {
  params.credential_type = selectedCredentialTypeId || 1;
  const { data } = await CredentialsAPI.read(params);
  return data;
}

function MultiCredentialsLookup({
  value,
  onChange,
  onError,
  history,
  fieldName,
  validate,
}) {
  const [selectedType, setSelectedType] = useState(null);
  const isMounted = useIsMounted();

  const {
    result: credentialTypes,
    request: fetchTypes,
    error: typesError,
    isLoading: isTypesLoading,
  } = useRequest(
    useCallback(async () => {
      const types = await CredentialTypesAPI.loadAllTypes();
      const match = types.find((type) => type.kind === 'ssh') || types[0];
      if (isMounted.current) {
        setSelectedType(match);
      }
      return types;
      /* eslint-disable-next-line react-hooks/exhaustive-deps */
    }, []),
    []
  );

  useEffect(() => {
    fetchTypes();
  }, [fetchTypes]);

  const {
    result: {
      credentials,
      credentialsCount,
      relatedSearchableKeys,
      searchableKeys,
    },
    request: fetchCredentials,
    error: credentialsError,
    isLoading: isCredentialsLoading,
  } = useRequest(
    useCallback(async () => {
      if (!selectedType) {
        return {
          credentials: [],
          credentialsCount: 0,
          relatedSearchableKeys: [],
          searchableKeys: [],
        };
      }

      const params = parseQueryString(QS_CONFIG, history.location.search);
      const [{ results, count }, actionsResponse] = await Promise.all([
        loadCredentials(params, selectedType.id),
        CredentialsAPI.readOptions(),
      ]);

      results.map((result) => {
        if (result.kind === 'vault' && result.inputs?.vault_id) {
          result.label = `${result.name} | ${result.inputs.vault_id}`;
          return result;
        }
        result.label = `${result.name}`;
        return result;
      });

      return {
        credentials: results,
        credentialsCount: count,
        relatedSearchableKeys: (
          actionsResponse?.data?.related_search_fields || []
        ).map((val) => val.slice(0, -8)),
        searchableKeys: getSearchableKeys(actionsResponse.data.actions?.GET),
      };
    }, [selectedType, history.location]),
    {
      credentials: [],
      credentialsCount: 0,
      relatedSearchableKeys: [],
      searchableKeys: [],
    }
  );

  useEffect(() => {
    fetchCredentials();
  }, [fetchCredentials]);

  useEffect(() => {
    if (typesError || credentialsError) {
      onError(typesError || credentialsError);
    }
  }, [typesError, credentialsError, onError]);

  const renderChip = ({ item, removeItem, canDelete }) => (
    <CredentialChip
      key={item.id}
      onClick={() => removeItem(item)}
      isReadOnly={!canDelete}
      credential={item}
    />
  );
  const isVault = selectedType?.kind === 'vault';

  return (
    <Lookup
      id="multiCredential"
      header={t`Credentials`}
      value={value}
      fieldName={fieldName}
      validate={validate}
      multiple
      onChange={onChange}
      onUpdate={fetchCredentials}
      qsConfig={QS_CONFIG}
      isLoading={isTypesLoading || isCredentialsLoading}
      renderItemChip={renderChip}
      renderOptionsList={({ state, dispatch, canDelete }) => (
        <>
          {isVault && (
            <Alert
              variant="info"
              isInline
              css="margin-bottom: 20px;"
              title={t`You cannot select multiple vault credentials with the same vault ID. Doing so will automatically deselect the other with the same vault ID.`}
              ouiaId="multi-credentials-lookup-alert"
            />
          )}
          {credentialTypes && credentialTypes.length > 0 && (
            <ToolbarItem css=" display: flex; align-items: center;">
              <div css="flex: 0 0 25%; margin-right: 32px">
                {t`Selected Category`}
              </div>
              <AnsibleSelect
                css="flex: 1 1 75%;"
                id="multiCredentialsLookUp-select"
                label={t`Selected Category`}
                data={credentialTypes.map((type) => ({
                  key: type.id,
                  value: type.id,
                  label: type.name,
                  isDisabled: false,
                }))}
                value={selectedType && selectedType.id}
                onChange={(e, id) => {
                  // Reset query params when the category of credentials is changed
                  history.replace({
                    search: '',
                  });
                  setSelectedType(
                    credentialTypes.find((o) => o.id === parseInt(id, 10))
                  );
                }}
              />
            </ToolbarItem>
          )}
          <OptionsList
            value={state.selectedItems}
            options={credentials}
            optionCount={credentialsCount}
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
            multiple={isVault}
            header={t`Credentials`}
            displayKey={isVault ? 'label' : 'name'}
            name="credentials"
            qsConfig={QS_CONFIG}
            readOnly={!canDelete}
            selectItem={(item) => {
              const hasSameVaultID = (val) =>
                val?.inputs?.vault_id !== undefined &&
                val?.inputs?.vault_id === item?.inputs?.vault_id;
              const hasSameCredentialType = (val) =>
                val.credential_type === item.credential_type;
              const selectedItems = state.selectedItems.filter((i) =>
                isVault ? !hasSameVaultID(i) : !hasSameCredentialType(i)
              );
              selectedItems.push(item);
              return dispatch({
                type: 'SET_SELECTED_ITEMS',
                selectedItems,
              });
            }}
            deselectItem={(item) => dispatch({ type: 'DESELECT_ITEM', item })}
            renderItemChip={renderChip}
          />
        </>
      )}
    />
  );
}

MultiCredentialsLookup.propTypes = {
  value: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.number,
      name: PropTypes.string,
      description: PropTypes.string,
      kind: PropTypes.string,
      clound: PropTypes.bool,
    })
  ),
  onChange: PropTypes.func.isRequired,
  onError: PropTypes.func.isRequired,
  validate: PropTypes.func,
  fieldName: PropTypes.string,
};

MultiCredentialsLookup.defaultProps = {
  value: [],
  validate: () => undefined,
  fieldName: 'credentials',
};

export { MultiCredentialsLookup as _MultiCredentialsLookup };
export default withRouter(MultiCredentialsLookup);
