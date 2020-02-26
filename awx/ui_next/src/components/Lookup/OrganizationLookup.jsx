import React, { useState, useEffect } from 'react';
import { node, func, bool } from 'prop-types';
import { withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { OrganizationsAPI } from '@api';
import { Organization } from '@types';
import { FormGroup } from '@patternfly/react-core';
import { getQSConfig, parseQueryString } from '@util/qs';
import Lookup from './Lookup';
import OptionsList from './shared/OptionsList';
import LookupErrorMessage from './shared/LookupErrorMessage';

const QS_CONFIG = getQSConfig('organizations', {
  page: 1,
  page_size: 5,
  order_by: 'name',
});

function OrganizationLookup({
  helperTextInvalid,
  i18n,
  isValid,
  onBlur,
  onChange,
  required,
  value,
  history,
}) {
  const [organizations, setOrganizations] = useState([]);
  const [count, setCount] = useState(0);
  const [error, setError] = useState(null);

  useEffect(() => {
    (async () => {
      const params = parseQueryString(QS_CONFIG, history.location.search);
      try {
        const { data } = await OrganizationsAPI.read(params);
        setOrganizations(data.results);
        setCount(data.count);
      } catch (err) {
        setError(err);
      }
    })();
  }, [history.location]);

  return (
    <FormGroup
      fieldId="organization"
      helperTextInvalid={helperTextInvalid}
      isRequired={required}
      isValid={isValid}
      label={i18n._(t`Organization`)}
    >
      <Lookup
        id="organization"
        header={i18n._(t`Organization`)}
        value={value}
        onBlur={onBlur}
        onChange={onChange}
        qsConfig={QS_CONFIG}
        required={required}
        sortedColumnKey="name"
        renderOptionsList={({ state, dispatch, canDelete }) => (
          <OptionsList
            value={state.selectedItems}
            options={organizations}
            optionCount={count}
            multiple={state.multiple}
            header={i18n._(t`Organization`)}
            name="organization"
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
            selectItem={item => dispatch({ type: 'SELECT_ITEM', item })}
            deselectItem={item => dispatch({ type: 'DESELECT_ITEM', item })}
          />
        )}
      />
      <LookupErrorMessage error={error} />
    </FormGroup>
  );
}

OrganizationLookup.propTypes = {
  helperTextInvalid: node,
  isValid: bool,
  onBlur: func,
  onChange: func.isRequired,
  required: bool,
  value: Organization,
};

OrganizationLookup.defaultProps = {
  helperTextInvalid: '',
  isValid: true,
  onBlur: () => {},
  required: false,
  value: null,
};

export { OrganizationLookup as _OrganizationLookup };
export default withI18n()(withRouter(OrganizationLookup));
