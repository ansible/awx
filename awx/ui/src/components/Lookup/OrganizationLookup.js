import React, { useCallback, useEffect } from 'react';
import { node, func, bool, string } from 'prop-types';
import { withRouter } from 'react-router-dom';
import { t } from '@lingui/macro';
import { FormGroup } from '@patternfly/react-core';
import { OrganizationsAPI } from 'api';
import { Organization } from 'types';
import { getQSConfig, parseQueryString } from 'util/qs';
import { getSearchableKeys } from 'components/PaginatedTable';
import useRequest from 'hooks/useRequest';
import useAutoPopulateLookup from 'hooks/useAutoPopulateLookup';
import OptionsList from '../OptionsList';
import Lookup from './Lookup';
import LookupErrorMessage from './shared/LookupErrorMessage';

const QS_CONFIG = getQSConfig('organizations', {
  page: 1,
  page_size: 5,
  order_by: 'name',
});

function OrganizationLookup({
  id,
  helperTextInvalid,
  isValid,
  onBlur,
  onChange,
  required,
  value,
  history,
  autoPopulate,
  isDisabled,
  helperText,
  validate,
  fieldName,
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
        ).map((val) => val.slice(0, -8)),
        searchableKeys: getSearchableKeys(actionsResponse.data.actions?.GET),
      };
    }, [autoPopulate, autoPopulateLookup, history.location.search]),
    {
      organizations: [],
      itemCount: 0,
      relatedSearchableKeys: [],
      searchableKeys: [],
    }
  );

  const checkOrganizationName = useCallback(
    async (name) => {
      if (!name) {
        onChange(null);
        return;
      }

      try {
        const {
          data: { results: nameMatchResults, count: nameMatchCount },
        } = await OrganizationsAPI.read({ name });
        onChange(nameMatchCount ? nameMatchResults[0] : null);
      } catch {
        onChange(null);
      }
    },
    [onChange]
  );

  useEffect(() => {
    fetchOrganizations();
  }, [fetchOrganizations]);

  return (
    <FormGroup
      fieldId={id}
      helperTextInvalid={helperTextInvalid}
      isRequired={required}
      validated={isValid ? 'default' : 'error'}
      label={t`Organization`}
      helperText={helperText}
    >
      <Lookup
        isDisabled={isDisabled}
        id={id}
        header={t`Organization`}
        value={value}
        onBlur={onBlur}
        onChange={onChange}
        onDebounce={checkOrganizationName}
        onUpdate={fetchOrganizations}
        fieldName={fieldName}
        validate={validate}
        qsConfig={QS_CONFIG}
        required={required}
        sortedColumnKey="name"
        renderOptionsList={({ state, dispatch, canDelete }) => (
          <OptionsList
            value={state.selectedItems}
            options={organizations}
            optionCount={itemCount}
            multiple={state.multiple}
            header={t`Organization`}
            name="organization"
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
            selectItem={(item) => dispatch({ type: 'SELECT_ITEM', item })}
            deselectItem={(item) => dispatch({ type: 'DESELECT_ITEM', item })}
          />
        )}
      />
      <LookupErrorMessage error={contentError} />
    </FormGroup>
  );
}

OrganizationLookup.propTypes = {
  id: string,
  helperTextInvalid: node,
  isValid: bool,
  onBlur: func,
  onChange: func.isRequired,
  required: bool,
  value: Organization,
  autoPopulate: bool,
  isDisabled: bool,
  validate: func,
  fieldName: string,
};

OrganizationLookup.defaultProps = {
  id: 'organization',
  helperTextInvalid: '',
  isValid: true,
  onBlur: () => {},
  required: false,
  value: null,
  autoPopulate: false,
  isDisabled: false,
  validate: () => undefined,
  fieldName: 'organization',
};

export { OrganizationLookup as _OrganizationLookup };
export default withRouter(OrganizationLookup);
