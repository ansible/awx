import React, { useCallback, useEffect } from 'react';
import { bool, func, node, number, string, oneOfType } from 'prop-types';
import { withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { FormGroup } from '@patternfly/react-core';
import { CredentialsAPI } from '../../api';
import { Credential } from '../../types';
import { getQSConfig, parseQueryString, mergeParams } from '../../util/qs';
import { FieldTooltip } from '../FormField';
import Lookup from './Lookup';
import OptionsList from '../OptionsList';
import useRequest from '../../util/useRequest';
import LookupErrorMessage from './shared/LookupErrorMessage';

const QS_CONFIG = getQSConfig('credentials', {
  page: 1,
  page_size: 5,
  order_by: 'name',
});

function CredentialLookup({
  helperTextInvalid,
  label,
  isValid,
  onBlur,
  onChange,
  required,
  credentialTypeId,
  credentialTypeKind,
  value,
  history,
  i18n,
  tooltip,
}) {
  const {
    result: { count, credentials },
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

      const { data } = await CredentialsAPI.read(
        mergeParams(params, { ...typeIdParams, ...typeKindParams })
      );
      return {
        count: data.count,
        credentials: data.results,
      };
    }, [credentialTypeId, credentialTypeKind, history.location.search]),
    {
      count: 0,
      credentials: [],
    }
  );

  useEffect(() => {
    fetchCredentials();
  }, [fetchCredentials]);

  // TODO: replace credential type search with REST-based grabbing of cred types

  return (
    <FormGroup
      fieldId="credential"
      isRequired={required}
      isValid={isValid}
      label={label}
      helperTextInvalid={helperTextInvalid}
    >
      {tooltip && <FieldTooltip content={tooltip} />}
      <Lookup
        id="credential"
        header={label}
        value={value}
        onBlur={onBlur}
        onChange={onChange}
        required={required}
        qsConfig={QS_CONFIG}
        renderOptionsList={({ state, dispatch, canDelete }) => (
          <OptionsList
            value={state.selectedItems}
            options={credentials}
            optionCount={count}
            header={label}
            qsConfig={QS_CONFIG}
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
            readOnly={!canDelete}
            name="credential"
            selectItem={item => dispatch({ type: 'SELECT_ITEM', item })}
            deselectItem={item => dispatch({ type: 'DESELECT_ITEM', item })}
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
  onBlur: func,
  onChange: func.isRequired,
  required: bool,
  value: Credential,
};

CredentialLookup.defaultProps = {
  credentialTypeId: '',
  credentialTypeKind: '',
  helperTextInvalid: '',
  isValid: true,
  onBlur: () => {},
  required: false,
  value: null,
};

export { CredentialLookup as _CredentialLookup };
export default withI18n()(withRouter(CredentialLookup));
