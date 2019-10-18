import React from 'react';
import { string, func, bool } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { FormGroup } from '@patternfly/react-core';
import { InventoriesAPI } from '@api';
import { Inventory } from '@types';
import Lookup from '@components/Lookup';
import { FieldTooltip } from '@components/FormField';

const getInventories = async params => InventoriesAPI.read(params);

class InventoryLookup extends React.Component {
  render() {
    const {
      value,
      tooltip,
      onChange,
      onBlur,
      required,
      isValid,
      helperTextInvalid,
      i18n,
    } = this.props;

    return (
      <FormGroup
        label={i18n._(t`Inventory`)}
        isRequired={required}
        fieldId="inventory-lookup"
        isValid={isValid}
        helperTextInvalid={helperTextInvalid}
      >
        {tooltip && <FieldTooltip content={tooltip} />}
        <Lookup
          id="inventory-lookup"
          lookupHeader={i18n._(t`Inventory`)}
          name="inventory"
          value={value}
          onLookupSave={onChange}
          onBlur={onBlur}
          getItems={getInventories}
          required={required}
          qsNamespace="inventory"
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

InventoryLookup.propTypes = {
  value: Inventory,
  tooltip: string,
  onChange: func.isRequired,
  required: bool,
};

InventoryLookup.defaultProps = {
  value: null,
  tooltip: '',
  required: false,
};

export default withI18n()(InventoryLookup);
