import React, { useCallback, useEffect } from 'react';
import { useHistory } from 'react-router-dom';
import {
  arrayOf,
  bool,
  func,
  node,
  number,
  string,
  oneOfType,
} from 'prop-types';

import { t } from '@lingui/macro';
import { FormGroup } from '@patternfly/react-core';
import { CredentialsAPI } from 'api';
import { Credential } from 'types';
import { getSearchableKeys } from 'components/PaginatedTable';
import { getQSConfig, parseQueryString, mergeParams } from 'util/qs';
import useAutoPopulateLookup from 'hooks/useAutoPopulateLookup';
import useRequest from 'hooks/useRequest';
import Popover from '../Popover';
import Lookup from './Lookup';
import OptionsList from '../OptionsList';
import LookupErrorMessage from './shared/LookupErrorMessage';

const QS_CONFIG = getQSConfig('credentials', {
  page: 1,
  page_size: 5,
  order_by: 'name',
});

function CredentialLookup({
  autoPopulate,
  credentialTypeId,
  credentialTypeKind,
  credentialTypeNamespace,
  fieldName,
  helperTextInvalid,
  isDisabled,
  isSelectedDraggable,
  isValid,
  label,
  modalDescription,
  multiple,
  onBlur,
  onChange,
  required,
  tooltip,
  validate,
  value,
}) {
  const history = useHistory();
  const autoPopulateLookup = useAutoPopulateLookup(onChange);
  const {
    result: { count, credentials, relatedSearchableKeys, searchableKeys },
    error,
    request: fetchCredentials,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, history.location.search);
      const typeIdParams = credentialTypeId
        ? { credential_type: credentialTypeId }
        : {};
      const typeKindParams = credentialTypeKind
        ? { credential_type__kind: credentialTypeKind }
        : {};
      const typeNamespaceParams = credentialTypeNamespace
        ? { credential_type__namespace: credentialTypeNamespace }
        : {};

      const [{ data }, actionsResponse] = await Promise.all([
        CredentialsAPI.read(
          mergeParams(params, {
            ...typeIdParams,
            ...typeKindParams,
            ...typeNamespaceParams,
          })
        ),
        CredentialsAPI.readOptions(),
      ]);

      if (autoPopulate) {
        autoPopulateLookup(data.results);
      }

      const searchKeys = getSearchableKeys(actionsResponse.data.actions?.GET);
      const item = searchKeys.find((k) => k.key === 'type');
      if (item) {
        item.key = 'credential_type__kind';
      }

      return {
        count: data.count,
        credentials: data.results,
        relatedSearchableKeys: (
          actionsResponse?.data?.related_search_fields || []
        ).map((val) => val.slice(0, -8)),
        searchableKeys: searchKeys,
      };
    }, [
      autoPopulate,
      autoPopulateLookup,
      credentialTypeId,
      credentialTypeKind,
      credentialTypeNamespace,
      history.location.search,
    ]),
    {
      count: 0,
      credentials: [],
      relatedSearchableKeys: [],
      searchableKeys: [],
    }
  );

  const checkCredentialName = useCallback(
    async (name) => {
      if (!name) {
        onChange(null);
        return;
      }

      try {
        const typeIdParams = credentialTypeId
          ? { credential_type: credentialTypeId }
          : {};
        const typeKindParams = credentialTypeKind
          ? { credential_type__kind: credentialTypeKind }
          : {};
        const typeNamespaceParams = credentialTypeNamespace
          ? { credential_type__namespace: credentialTypeNamespace }
          : {};

        const {
          data: { results: nameMatchResults, count: nameMatchCount },
        } = await CredentialsAPI.read({
          name,
          ...typeIdParams,
          ...typeKindParams,
          ...typeNamespaceParams,
        });
        onChange(nameMatchCount ? nameMatchResults[0] : null);
      } catch {
        onChange(null);
      }
    },
    [onChange, credentialTypeId, credentialTypeKind, credentialTypeNamespace]
  );

  useEffect(() => {
    fetchCredentials();
  }, [fetchCredentials]);

  // TODO: replace credential type search with REST-based grabbing of cred types

  return (
    <FormGroup
      fieldId="credential"
      isRequired={required}
      validated={isValid ? 'default' : 'error'}
      label={label}
      labelIcon={tooltip && <Popover content={tooltip} />}
      helperTextInvalid={helperTextInvalid}
    >
      <Lookup
        id="credential"
        header={label}
        value={value}
        onBlur={onBlur}
        onChange={onChange}
        onUpdate={fetchCredentials}
        onDebounce={checkCredentialName}
        fieldName={fieldName}
        validate={validate}
        required={required}
        qsConfig={QS_CONFIG}
        isDisabled={isDisabled}
        multiple={multiple}
        modalDescription={modalDescription}
        renderOptionsList={({ state, dispatch, canDelete }) => (
          <OptionsList
            value={state.selectedItems}
            options={credentials}
            optionCount={count}
            header={label}
            qsConfig={QS_CONFIG}
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
            readOnly={!canDelete}
            name="credential"
            selectItem={(item) => dispatch({ type: 'SELECT_ITEM', item })}
            deselectItem={(item) => dispatch({ type: 'DESELECT_ITEM', item })}
            sortSelectedItems={(selectedItems) =>
              dispatch({ type: 'SET_SELECTED_ITEMS', selectedItems })
            }
            multiple={multiple}
            isSelectedDraggable={isSelectedDraggable}
          />
        )}
      />
      <LookupErrorMessage error={error} />
    </FormGroup>
  );
}

function idOrKind(props, propName, componentName) {
  let error;
  if (
    !Object.prototype.hasOwnProperty.call(props, 'credentialTypeId') &&
    !Object.prototype.hasOwnProperty.call(props, 'credentialTypeKind')
  )
    error = new Error(
      `Either "credentialTypeId" or "credentialTypeKind" is required`
    );
  if (
    !Object.prototype.hasOwnProperty.call(props, 'credentialTypeId') &&
    typeof props[propName] !== 'string'
  ) {
    error = new Error(
      `Invalid prop '${propName}' '${props[propName]}' supplied to '${componentName}'.`
    );
  }
  return error;
}

CredentialLookup.propTypes = {
  credentialTypeId: oneOfType([number, string]),
  credentialTypeKind: idOrKind,
  helperTextInvalid: node,
  isValid: bool,
  label: string.isRequired,
  multiple: bool,
  onBlur: func,
  onChange: func.isRequired,
  required: bool,
  value: oneOfType([Credential, arrayOf(Credential)]),
  isDisabled: bool,
  autoPopulate: bool,
  validate: func,
  fieldName: string,
};

CredentialLookup.defaultProps = {
  credentialTypeId: '',
  credentialTypeKind: '',
  helperTextInvalid: '',
  isValid: true,
  multiple: false,
  onBlur: () => {},
  required: false,
  value: null,
  isDisabled: false,
  autoPopulate: false,
  validate: () => undefined,
  fieldName: 'credential',
};

export { CredentialLookup as _CredentialLookup };
export default CredentialLookup;
