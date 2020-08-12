import 'styled-components/macro';
import React, { useState, useCallback, useEffect } from 'react';
import { useHistory } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { useField } from 'formik';
import { ToolbarItem } from '@patternfly/react-core';
import { CredentialsAPI, CredentialTypesAPI } from '../../../api';
import AnsibleSelect from '../../AnsibleSelect';
import OptionsList from '../../OptionsList';
import ContentLoading from '../../ContentLoading';
import CredentialChip from '../../CredentialChip';
import ContentError from '../../ContentError';
import { getQSConfig, parseQueryString } from '../../../util/qs';
import useRequest from '../../../util/useRequest';
import { required } from '../../../util/validators';

const QS_CONFIG = getQSConfig('credential', {
  page: 1,
  page_size: 5,
  order_by: 'name',
});

function CredentialsStep({ i18n }) {
  const [field, , helpers] = useField({
    name: 'credentials',
    validate: required(null, i18n),
  });
  const [selectedType, setSelectedType] = useState(null);
  const history = useHistory();

  const {
    result: types,
    error: typesError,
    isLoading: isTypesLoading,
    request: fetchTypes,
  } = useRequest(
    useCallback(async () => {
      const loadedTypes = await CredentialTypesAPI.loadAllTypes();
      if (loadedTypes.length) {
        const match =
          loadedTypes.find(type => type.kind === 'ssh') || loadedTypes[0];
        setSelectedType(match);
      }
      return loadedTypes;
    }, []),
    []
  );

  useEffect(() => {
    fetchTypes();
  }, [fetchTypes]);

  const {
    result: { credentials, count, relatedSearchableKeys, searchableKeys },
    error: credentialsError,
    isLoading: isCredentialsLoading,
    request: fetchCredentials,
  } = useRequest(
    useCallback(async () => {
      if (!selectedType) {
        return { credentials: [], count: 0 };
      }
      const params = parseQueryString(QS_CONFIG, history.location.search);
      const [{ data }, actionsResponse] = await Promise.all([
        CredentialsAPI.read({
          ...params,
          credential_type: selectedType.id,
        }),
        CredentialsAPI.readOptions(),
      ]);
      return {
        credentials: data.results,
        count: data.count,
        relatedSearchableKeys: (
          actionsResponse?.data?.related_search_fields || []
        ).map(val => val.slice(0, -8)),
        searchableKeys: Object.keys(
          actionsResponse.data.actions?.GET || {}
        ).filter(key => actionsResponse.data.actions?.GET[key].filterable),
      };
    }, [selectedType, history.location.search]),
    { credentials: [], count: 0, relatedSearchableKeys: [], searchableKeys: [] }
  );

  useEffect(() => {
    fetchCredentials();
  }, [fetchCredentials]);

  if (isTypesLoading) {
    return <ContentLoading />;
  }

  if (typesError || credentialsError) {
    return <ContentError error={typesError || credentialsError} />;
  }

  const isVault = selectedType?.kind === 'vault';

  const renderChip = ({ item, removeItem, canDelete }) => (
    <CredentialChip
      key={item.id}
      onClick={() => removeItem(item)}
      isReadOnly={!canDelete}
      credential={item}
    />
  );

  return (
    <>
      {types && types.length > 0 && (
        <ToolbarItem css=" display: flex; align-items: center;">
          <div css="flex: 0 0 25%; margin-right: 32px">
            {i18n._(t`Selected Category`)}
          </div>
          <AnsibleSelect
            css="flex: 1 1 75%;"
            id="multiCredentialsLookUp-select"
            label={i18n._(t`Selected Category`)}
            data={types.map(type => ({
              key: type.id,
              value: type.id,
              label: type.name,
              isDisabled: false,
            }))}
            value={selectedType && selectedType.id}
            onChange={(e, id) => {
              setSelectedType(types.find(o => o.id === parseInt(id, 10)));
            }}
          />
        </ToolbarItem>
      )}
      {!isCredentialsLoading && (
        <OptionsList
          value={field.value || []}
          options={credentials}
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
          multiple={isVault}
          header={i18n._(t`Credentials`)}
          name="credentials"
          qsConfig={QS_CONFIG}
          readOnly={false}
          selectItem={item => {
            const hasSameVaultID = val =>
              val?.inputs?.vault_id !== undefined &&
              val?.inputs?.vault_id === item?.inputs?.vault_id;
            const hasSameKind = val => val.kind === item.kind;
            const newItems = field.value.filter(i =>
              isVault ? !hasSameVaultID(i) : !hasSameKind(i)
            );
            newItems.push(item);
            helpers.setValue(newItems);
          }}
          deselectItem={item => {
            helpers.setValue(field.value.filter(i => i.id !== item.id));
          }}
          renderItemChip={renderChip}
        />
      )}
    </>
  );
}

export default withI18n()(CredentialsStep);
