import React, { Fragment } from 'react';
import { string, func, bool } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { FormGroup, Tooltip } from '@patternfly/react-core';
import { QuestionCircleIcon } from '@patternfly/react-icons';

import { InventoriesAPI } from '@api';
import { Inventory } from '@types';
import Lookup from '@components/Lookup';

const getInventories = async params => InventoriesAPI.read(params);

class InventoriesLookup extends React.Component {
  render() {
    const { value, tooltip, onChange, required, i18n } = this.props;

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
          required={required}
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
  value: Inventory,
  tooltip: string,
  onChange: func.isRequired,
  required: bool,
};

InventoriesLookup.defaultProps = {
  value: null,
  tooltip: '',
  required: false,
};

export default withI18n()(InventoriesLookup);
