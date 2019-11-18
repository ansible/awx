import React, { useState, useEffect } from 'react';
import { arrayOf, string, func, object } from 'prop-types';
import { withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { FormGroup, Tooltip } from '@patternfly/react-core';
import { QuestionCircleIcon as PFQuestionCircleIcon } from '@patternfly/react-icons';
import styled from 'styled-components';
import { InstanceGroupsAPI } from '@api';
import { getQSConfig, parseQueryString } from '@util/qs';
import Lookup from './NewLookup';

const QuestionCircleIcon = styled(PFQuestionCircleIcon)`
  margin-left: 10px;
`;

const QS_CONFIG = getQSConfig('instance-groups', {
  page: 1,
  page_size: 5,
  order_by: 'name',
});
// const getInstanceGroups = async params => InstanceGroupsAPI.read(params);

function InstanceGroupsLookup({
  value,
  onChange,
  tooltip,
  className,
  history,
  i18n,
}) {
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

  /*
      Wrapping <div> added to workaround PF bug:
      https://github.com/patternfly/patternfly-react/issues/2855
    */
  return (
    <div className={className}>
      <FormGroup
        label={i18n._(t`Instance Groups`)}
        fieldId="org-instance-groups"
      >
        {tooltip && (
          <Tooltip position="right" content={tooltip}>
            <QuestionCircleIcon />
          </Tooltip>
        )}
        <Lookup
          id="org-instance-groups"
          lookupHeader={i18n._(t`Instance Groups`)}
          name="instanceGroups"
          value={value}
          onChange={onChange}
          items={instanceGroups}
          count={count}
          qsConfig={QS_CONFIG}
          multiple
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
          sortedColumnKey="name"
        />
        {error ? <div>error {error.message}</div> : ''}
      </FormGroup>
    </div>
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
