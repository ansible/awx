import React, { Fragment } from 'react';
import PropTypes from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { FormGroup, Tooltip } from '@patternfly/react-core';
import { QuestionCircleIcon } from '@patternfly/react-icons';

import Lookup from '../../../components/Lookup';

import { InstanceGroupsAPI } from '../../../api';

const getInstanceGroups = async (params) => InstanceGroupsAPI.read(params);

class InstanceGroupsLookup extends React.Component {
  render () {
    const { value, tooltip, onChange, i18n } = this.props;

    return (
      <FormGroup
        label={(
          <Fragment>
            {i18n._(t`Instance Groups`)}
            {' '}
            {
              tooltip && (
                <Tooltip
                  position="right"
                  content={tooltip}
                >
                  <QuestionCircleIcon />
                </Tooltip>
              )
            }
          </Fragment>
        )}
        fieldId="org-instance-groups"
      >
        <Lookup
          id="org-instance-groups"
          lookupHeader={i18n._(t`Instance Groups`)}
          name="instanceGroups"
          value={value}
          onLookupSave={onChange}
          getItems={getInstanceGroups}
          columns={[
            { name: i18n._(t`Name`), key: 'name', isSortable: true },
            { name: i18n._(t`Modified`), key: 'modified', isSortable: false, isNumeric: true },
            { name: i18n._(t`Created`), key: 'created', isSortable: false, isNumeric: true }
          ]}
          sortedColumnKey="name"
        />
      </FormGroup>
    );
  }
}

InstanceGroupsLookup.propTypes = {
  value: PropTypes.arrayOf(PropTypes.object).isRequired,
  tooltip: PropTypes.string,
  onChange: PropTypes.func.isRequired,
};

InstanceGroupsLookup.defaultProps = {
  tooltip: '',
};

export default withI18n()(InstanceGroupsLookup);
