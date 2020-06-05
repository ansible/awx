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
    result: { instanceGroups, count },
    request: fetchInstanceGroups,
    error,
    isLoading,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, history.location.search);
      const { data } = await InstanceGroupsAPI.read(params);
      return {
        instanceGroups: data.results,
        count: data.count,
      };
    }, [history.location]),
    { instanceGroups: [], count: 0 }
  );

  useEffect(() => {
    fetchInstanceGroups();
  }, [fetchInstanceGroups]);

  return (
    <FormGroup
      className={className}
      label={i18n._(t`Instance Groups`)}
      fieldId="org-instance-groups"
    >
      {tooltip && <FieldTooltip content={tooltip} />}
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
                key: 'name',
                isDefault: true,
              },
              {
                name: i18n._(t`Credential Name`),
                key: 'credential__name',
              },
            ]}
            sortColumns={[
              {
                name: i18n._(t`Name`),
                key: 'name',
              },
            ]}
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
