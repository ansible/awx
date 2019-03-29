import React, { Fragment } from 'react';
import PropTypes from 'prop-types';
import { I18n, i18nMark } from '@lingui/react';
import { FormGroup, Tooltip } from '@patternfly/react-core';
import { QuestionCircleIcon } from '@patternfly/react-icons';
import { t } from '@lingui/macro';

import Lookup from '../../../components/Lookup';

const INSTANCE_GROUPS_LOOKUP_COLUMNS = [
  { name: i18nMark('Name'), key: 'name', isSortable: true },
  { name: i18nMark('Modified'), key: 'modified', isSortable: false, isNumeric: true },
  { name: i18nMark('Created'), key: 'created', isSortable: false, isNumeric: true }
];

class InstanceGroupsLookup extends React.Component {
  constructor (props) {
    super(props);

    this.getInstanceGroups = this.getInstanceGroups.bind(this);
  }

  async getInstanceGroups (params) {
    const { api } = this.props;
    const data = await api.getInstanceGroups(params);
    return data;
  }

  render () {
    const { value, tooltip, onChange } = this.props;

    return (
      <I18n>
        {({ i18n }) => (
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
            fieldId="add-org-form-instance-groups"
          >
            <Lookup
              lookupHeader={i18n._(t`Instance Groups`)}
              name="instanceGroups"
              value={value}
              onLookupSave={onChange}
              getItems={this.getInstanceGroups}
              columns={INSTANCE_GROUPS_LOOKUP_COLUMNS}
              sortedColumnKey="name"
            />
          </FormGroup>
        )}
      </I18n>
    );
  }
}

InstanceGroupsLookup.propTypes = {
  api: PropTypes.shape({
    getInstanceGroups: PropTypes.func,
  }).isRequired,
  value: PropTypes.arrayOf(PropTypes.object).isRequired,
  tooltip: PropTypes.string,
  onChange: PropTypes.func.isRequired,
};

InstanceGroupsLookup.defaultProps = {
  tooltip: '',
};

export default InstanceGroupsLookup;
