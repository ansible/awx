import React from 'react';
import { string, func, bool } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { FormGroup, Tooltip } from '@patternfly/react-core';
import { QuestionCircleIcon as PFQuestionCircleIcon} from '@patternfly/react-icons';
import styled from 'styled-components';

import { InventoriesAPI } from '@api';
import { Inventory } from '@types';
import Lookup from '@components/Lookup';

const QuestionCircleIcon = styled(PFQuestionCircleIcon)`
  margin-left: 10px;
`;

const getInventories = async params => InventoriesAPI.read(params);

class InventoryLookup extends React.Component {
  render() {
    const { value, tooltip, onChange, required, i18n } = this.props;

    return (
      <FormGroup
        label={i18n._(t`Inventory`)}
        isRequired={required}
        fieldId="inventory-lookup"
      >
        {tooltip && (
          <Tooltip position="right" content={tooltip}>
            <QuestionCircleIcon />
          </Tooltip>
        )}
        <Lookup
          id="inventory-lookup"
          lookupHeader={i18n._(t`Inventory`)}
          name="inventory"
          value={value}
          onLookupSave={onChange}
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
