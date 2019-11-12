import React, { Fragment } from 'react';
import PropTypes from 'prop-types';

import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import CheckboxCard from './CheckboxCard';
import SelectedList from '../SelectedList';

class RolesStep extends React.Component {
  render() {
    const {
      onRolesClick,
      roles,
      selectedListKey,
      selectedListLabel,
      selectedResourceRows,
      selectedRoleRows,
      i18n,
    } = this.props;

    return (
      <Fragment>
        <div>
          {i18n._(
            t`Choose roles to apply to the selected resources.  Note that all selected roles will be applied to all selected resources.`
          )}
        </div>
        <div>
          {selectedResourceRows.length > 0 && (
            <SelectedList
              displayKey={selectedListKey}
              isReadOnly
              label={selectedListLabel || i18n._(t`Selected`)}
              selected={selectedResourceRows}
            />
          )}
        </div>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: '20px 20px',
            marginTop: '20px',
          }}
        >
          {Object.keys(roles).map(role => (
            <CheckboxCard
              description={roles[role].description}
              itemId={roles[role].id}
              isSelected={selectedRoleRows.some(
                item => item.id === roles[role].id
              )}
              key={roles[role].id}
              name={roles[role].name}
              onSelect={() => onRolesClick(roles[role])}
            />
          ))}
        </div>
      </Fragment>
    );
  }
}

RolesStep.propTypes = {
  onRolesClick: PropTypes.func,
  roles: PropTypes.objectOf(PropTypes.object).isRequired,
  selectedListKey: PropTypes.string,
  selectedListLabel: PropTypes.string,
  selectedResourceRows: PropTypes.arrayOf(PropTypes.object),
  selectedRoleRows: PropTypes.arrayOf(PropTypes.object),
};

RolesStep.defaultProps = {
  onRolesClick: () => {},
  selectedListKey: 'name',
  selectedListLabel: null,
  selectedResourceRows: [],
  selectedRoleRows: [],
};

export default withI18n()(RolesStep);
