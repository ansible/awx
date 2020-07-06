import React, { useCallback, useEffect } from 'react';
import { func, node } from 'prop-types';
import { withRouter, useLocation } from 'react-router-dom';
import { withI18n } from '@lingui/react';
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

function ApplicationLookup({ i18n, onChange, value, label }) {
  const location = useLocation();
  const {
    error,
    result: { applications, itemCount },
    request: fetchApplications,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, location.search);

      const {
        data: { results, count },
      } = await ApplicationsAPI.read(params);
      return { applications: results, itemCount: count };
    }, [location]),
    { applications: [], itemCount: 0 }
  );
  useEffect(() => {
    fetchApplications();
  }, [fetchApplications]);
  return (
    <FormGroup fieldId="application" label={label}>
      <Lookup
        id="application"
        header={i18n._(t`Application`)}
        value={value}
        onChange={onChange}
        qsConfig={QS_CONFIG}
        renderOptionsList={({ state, dispatch, canDelete }) => (
          <OptionsList
            value={state.selectedItems}
            options={applications}
            optionCount={itemCount}
            header={i18n._(t`Applications`)}
            qsConfig={QS_CONFIG}
            searchColumns={[
              {
                name: i18n._(t`Name`),
                key: 'name',
                isDefault: true,
              },
              {
                name: i18n._(t`Description`),
                key: 'description',
              },
            ]}
            sortColumns={[
              {
                name: i18n._(t`Name`),
                key: 'name',
              },
              {
                name: i18n._(t`Created`),
                key: 'created',
              },
              {
                name: i18n._(t`Organization`),
                key: 'organization',
              },
              {
                name: i18n._(t`Description`),
                key: 'description',
              },
            ]}
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

export default withI18n()(withRouter(ApplicationLookup));
