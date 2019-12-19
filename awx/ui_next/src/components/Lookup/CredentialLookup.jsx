import React, { useEffect, useState } from 'react';
import { bool, func, number, string, oneOfType } from 'prop-types';
import { withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { CredentialsAPI } from '@api';
import { Credential } from '@types';
import { getQSConfig, parseQueryString, mergeParams } from '@util/qs';
import { FormGroup } from '@patternfly/react-core';
import Lookup from '@components/Lookup';
import OptionsList from './shared/OptionsList';
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
  value,
  history,
}) {
  const [credentials, setCredentials] = useState([]);
  const [count, setCount] = useState(0);
  const [error, setError] = useState(null);

  useEffect(() => {
    (async () => {
      const params = parseQueryString(QS_CONFIG, history.location.search);
      try {
        const { data } = await CredentialsAPI.read(
          mergeParams(params, { credential_type: credentialTypeId })
        );
        setCredentials(data.results);
        setCount(data.count);
      } catch (err) {
        if (setError) {
          setError(err);
        }
      }
    })();
  }, [credentialTypeId, history.location.search]);

  return (
    <FormGroup
      fieldId="credential"
      isRequired={required}
      isValid={isValid}
      label={label}
      helperTextInvalid={helperTextInvalid}
    >
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
            readOnly={!canDelete}
            selectItem={item => dispatch({ type: 'SELECT_ITEM', item })}
            deselectItem={item => dispatch({ type: 'DESELECT_ITEM', item })}
          />
        )}
      />
      <LookupErrorMessage error={error} />
    </FormGroup>
  );
}

CredentialLookup.propTypes = {
  credentialTypeId: oneOfType([number, string]).isRequired,
  helperTextInvalid: string,
  isValid: bool,
  label: string.isRequired,
  onBlur: func,
  onChange: func.isRequired,
  required: bool,
  value: Credential,
};

CredentialLookup.defaultProps = {
  helperTextInvalid: '',
  isValid: true,
  onBlur: () => {},
  required: false,
  value: null,
};

export { CredentialLookup as _CredentialLookup };
export default withI18n()(withRouter(CredentialLookup));
