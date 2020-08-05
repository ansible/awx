import React, { useCallback, useEffect } from 'react';
import { arrayOf, string, func, object, bool } from 'prop-types';
import { withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { FormGroup } from '@patternfly/react-core';
import { InstanceGroupsAPI } from '../../api';
import { getQSConfig, parseQueryString } from '../../util/qs';
import { FieldTooltip } from '../FormField';
import OptionsList from '../OptionsList';
import useRequest from '../../util/useRequest';
import Lookup from './Lookup';
import LookupErrorMessage from './shared/LookupErrorMessage';

const QS_CONFIG = getQSConfig('instance_groups', {
  page: 1,
  page_size: 5,
  order_by: 'name',
});

function InstanceGroupsLookup(props) {
  const {
    value,
    onChange,
    tooltip,
    className,
    required,
    history,
    i18n,
  } = props;

  const {
    result: { instanceGroups, count, actions, relatedSearchFields },
    request: fetchInstanceGroups,
    error,
    isLoading,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, history.location.search);
      const [{ data }, actionsResponse] = await Promise.all([
        InstanceGroupsAPI.read(params),
        InstanceGroupsAPI.readOptions(),
      ]);
      return {
        instanceGroups: data.results,
        count: data.count,
        actions: actionsResponse.data.actions,
        relatedSearchFields: (
          actionsResponse?.data?.related_search_fields || []
        ).map(val => val.slice(0, -8)),
      };
    }, [history.location]),
    { instanceGroups: [], count: 0, actions: {}, relatedSearchFields: [] }
  );

  useEffect(() => {
    fetchInstanceGroups();
  }, [fetchInstanceGroups]);

  const relatedSearchableKeys = relatedSearchFields || [];
  const searchableKeys = Object.keys(actions?.GET || {}).filter(
    key => actions.GET[key].filterable
  );

  return (
    <FormGroup
      className={className}
      label={i18n._(t`Instance Groups`)}
      labelIcon={tooltip && <FieldTooltip content={tooltip} />}
      fieldId="org-instance-groups"
    >
      <Lookup
        id="org-instance-groups"
        header={i18n._(t`Instance Groups`)}
        value={value}
        onChange={onChange}
        qsConfig={QS_CONFIG}
        multiple
        required={required}
        isLoading={isLoading}
        renderOptionsList={({ state, dispatch, canDelete }) => (
          <OptionsList
            value={state.selectedItems}
            options={instanceGroups}
            optionCount={count}
            searchColumns={[
              {
                name: i18n._(t`Name`),
                key: 'name__icontains',
                isDefault: true,
              },
              {
                name: i18n._(t`Credential Name`),
                key: 'credential__name__icontains',
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
            multiple={state.multiple}
            header={i18n._(t`Instance Groups`)}
            name="instanceGroups"
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

InstanceGroupsLookup.propTypes = {
  value: arrayOf(object).isRequired,
  tooltip: string,
  onChange: func.isRequired,
  className: string,
  required: bool,
};

InstanceGroupsLookup.defaultProps = {
  tooltip: '',
  className: '',
  required: false,
};

export default withI18n()(withRouter(InstanceGroupsLookup));
