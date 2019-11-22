import React, { useState, useEffect } from 'react';
import { arrayOf, string, func, object } from 'prop-types';
import { withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { FormGroup } from '@patternfly/react-core';
import { InstanceGroupsAPI } from '@api';
import { getQSConfig, parseQueryString } from '@util/qs';
import { FieldTooltip } from '@components/FormField';
import Lookup from './NewLookup';
import SelectList from './shared/SelectList';

const QS_CONFIG = getQSConfig('instance_groups', {
  page: 1,
  page_size: 5,
  order_by: 'name',
});

function InstanceGroupsLookup(props) {
  const { value, onChange, tooltip, className, history, i18n } = props;
  const [instanceGroups, setInstanceGroups] = useState([]);
  const [count, setCount] = useState(0);
  const [error, setError] = useState(null);

  useEffect(() => {
    (async () => {
      const params = parseQueryString(QS_CONFIG, history.location.search);
      try {
        const { data } = await InstanceGroupsAPI.read(params);
        setInstanceGroups(data.results);
        setCount(data.count);
      } catch (err) {
        setError(err);
      }
    })();
  }, [history.location]);

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
        // name="instanceGroups"
        value={value}
        onChange={onChange}
        // items={instanceGroups}
        // count={count}
        qsConfig={QS_CONFIG}
        multiple
        // columns={}
        sortedColumnKey="name"
        renderSelectList={({ state, dispatch, canDelete }) => (
          <SelectList
            value={state.selectedItems}
            options={instanceGroups}
            optionCount={count}
            columns={[
              {
                name: i18n._(t`Name`),
                key: 'name',
                isSortable: true,
                isSearchable: true,
              },
              {
                name: i18n._(t`Modified`),
                key: 'modified',
                isSortable: false,
                isNumeric: true,
              },
              {
                name: i18n._(t`Created`),
                key: 'created',
                isSortable: false,
                isNumeric: true,
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
      {error ? <div>error {error.message}</div> : ''}
    </FormGroup>
  );
}

InstanceGroupsLookup.propTypes = {
  value: arrayOf(object).isRequired,
  tooltip: string,
  onChange: func.isRequired,
  className: string,
};

InstanceGroupsLookup.defaultProps = {
  tooltip: '',
  className: '',
};

export default withI18n()(withRouter(InstanceGroupsLookup));
