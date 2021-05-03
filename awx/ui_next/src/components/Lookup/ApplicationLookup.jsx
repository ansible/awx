import React, { useCallback, useEffect } from 'react';
import { func, node } from 'prop-types';
import { withRouter, useLocation } from 'react-router-dom';

import { t } from '@lingui/macro';
import { FormGroup } from '@patternfly/react-core';
import { ApplicationsAPI } from '../../api';
import { Application } from '../../types';
import { getQSConfig, parseQueryString } from '../../util/qs';
import Lookup from './Lookup';
import OptionsList from '../OptionsList';
import useRequest from '../../util/useRequest';
import LookupErrorMessage from './shared/LookupErrorMessage';

const QS_CONFIG = getQSConfig('applications', {
  page: 1,
  page_size: 5,
  order_by: 'name',
});

function ApplicationLookup({ onChange, value, label }) {
  const location = useLocation();
  const {
    error,
    result: { applications, itemCount, relatedSearchableKeys, searchableKeys },
    request: fetchApplications,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, location.search);

      const [
        {
          data: { results, count },
        },
        actionsResponse,
      ] = await Promise.all([
        ApplicationsAPI.read(params),
        ApplicationsAPI.readOptions,
      ]);
      return {
        applications: results,
        itemCount: count,
        relatedSearchableKeys: (
          actionsResponse?.data?.related_search_fields || []
        ).map(val => val.slice(0, -8)),
        searchableKeys: Object.keys(
          actionsResponse?.data?.actions?.GET || {}
        ).filter(key => actionsResponse.data.actions?.GET[key].filterable),
      };
    }, [location]),
    {
      applications: [],
      itemCount: 0,
      relatedSearchableKeys: [],
      searchableKeys: [],
    }
  );
  useEffect(() => {
    fetchApplications();
  }, [fetchApplications]);
  return (
    <FormGroup fieldId="application" label={label}>
      <Lookup
        id="application"
        header={t`Application`}
        value={value}
        onChange={onChange}
        qsConfig={QS_CONFIG}
        renderOptionsList={({ state, dispatch, canDelete }) => (
          <OptionsList
            value={state.selectedItems}
            options={applications}
            optionCount={itemCount}
            header={t`Applications`}
            qsConfig={QS_CONFIG}
            searchColumns={[
              {
                name: t`Name`,
                key: 'name__icontains',
                isDefault: true,
              },
              {
                name: t`Description`,
                key: 'description__icontains',
              },
            ]}
            sortColumns={[
              {
                name: t`Name`,
                key: 'name',
              },
              {
                name: t`Created`,
                key: 'created',
              },
              {
                name: t`Organization`,
                key: 'organization',
              },
              {
                name: t`Description`,
                key: 'description',
              },
            ]}
            searchableKeys={searchableKeys}
            relatedSearchableKeys={relatedSearchableKeys}
            readOnly={!canDelete}
            name="application"
            selectItem={item => dispatch({ type: 'SELECT_ITEM', item })}
            deselectItem={item => dispatch({ type: 'DESELECT_ITEM', item })}
          />
        )}
      />
      <LookupErrorMessage error={error} />
    </FormGroup>
  );
}
ApplicationLookup.propTypes = {
  label: node.isRequired,
  onChange: func.isRequired,
  value: Application,
};

ApplicationLookup.defaultProps = {
  value: null,
};

export default withRouter(ApplicationLookup);
