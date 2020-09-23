import React, { useCallback, useEffect } from 'react';
import { node, func, bool } from 'prop-types';
import { withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { FormGroup } from '@patternfly/react-core';
import { OrganizationsAPI } from '../../api';
import { Organization } from '../../types';
import { getQSConfig, parseQueryString } from '../../util/qs';
import useRequest from '../../util/useRequest';
import useAutoPopulateLookup from '../../util/useAutoPopulateLookup';
import OptionsList from '../OptionsList';
import Lookup from './Lookup';
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
  autoPopulate,
}) {
  const autoPopulateLookup = useAutoPopulateLookup(onChange);

  const {
    result: { itemCount, organizations, relatedSearchableKeys, searchableKeys },
    error: contentError,
    request: fetchOrganizations,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, history.location.search);
      const [response, actionsResponse] = await Promise.all([
        OrganizationsAPI.read(params),
        OrganizationsAPI.readOptions(),
      ]);

      if (autoPopulate) {
        autoPopulateLookup(response.data.results);
      }

      return {
        organizations: response.data.results,
        itemCount: response.data.count,
        relatedSearchableKeys: (
          actionsResponse?.data?.related_search_fields || []
        ).map(val => val.slice(0, -8)),
        searchableKeys: Object.keys(
          actionsResponse.data.actions?.GET || {}
        ).filter(key => actionsResponse.data.actions?.GET[key].filterable),
      };
    }, [autoPopulate, autoPopulateLookup, history.location.search]),
    {
      organizations: [],
      itemCount: 0,
      relatedSearchableKeys: [],
      searchableKeys: [],
    }
  );

  useEffect(() => {
    fetchOrganizations();
  }, [fetchOrganizations]);

  return (
    <FormGroup
      fieldId="organization"
      helperTextInvalid={helperTextInvalid}
      isRequired={required}
      validated={isValid ? 'default' : 'error'}
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
            optionCount={itemCount}
            multiple={state.multiple}
            header={i18n._(t`Organization`)}
            name="organization"
            qsConfig={QS_CONFIG}
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
            readOnly={!canDelete}
            selectItem={item => dispatch({ type: 'SELECT_ITEM', item })}
            deselectItem={item => dispatch({ type: 'DESELECT_ITEM', item })}
          />
        )}
      />
      <LookupErrorMessage error={contentError} />
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
  autoPopulate: bool,
};

OrganizationLookup.defaultProps = {
  helperTextInvalid: '',
  isValid: true,
  onBlur: () => {},
  required: false,
  value: null,
  autoPopulate: false,
};

export { OrganizationLookup as _OrganizationLookup };
export default withI18n()(withRouter(OrganizationLookup));
