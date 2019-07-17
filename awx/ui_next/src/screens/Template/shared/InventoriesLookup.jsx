import React, { Fragment } from 'react';
import PropTypes from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { FormGroup, Tooltip } from '@patternfly/react-core';
import { QuestionCircleIcon } from '@patternfly/react-icons';

import { InventoriesAPI } from '@api';
import Lookup from '@components/Lookup';

const getInventories = async params => InventoriesAPI.read(params);

class InventoriesLookup extends React.Component {
  render() {
    const { value, tooltip, onChange, i18n } = this.props;

    return (
      <FormGroup
        label={
          <Fragment>
            {i18n._(t`Inventories`)}{' '}
            {tooltip && (
              <Tooltip position="right" content={tooltip}>
                <QuestionCircleIcon />
              </Tooltip>
            )}
          </Fragment>
        }
        fieldId="inventories-lookup"
      >
        <Lookup
          id="inventories-lookup"
          lookupHeader={i18n._(t`Inventories`)}
          name="inventories"
          value={value}
          onLookupSave={onChange}
          getItems={getInventories}
          multiple
          columns={[
            { name: i18n._(t`Name`), key: 'name', isSortable: true },
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
      </FormGroup>
    );
  }
}

InventoriesLookup.propTypes = {
  value: PropTypes.arrayOf(PropTypes.object).isRequired,
  tooltip: PropTypes.string,
  onChange: PropTypes.func.isRequired,
};

InventoriesLookup.defaultProps = {
  tooltip: '',
};

export default withI18n()(InventoriesLookup);
