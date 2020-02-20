import React, { Fragment } from 'react';
import {
  func,
  bool,
  number,
  string,
  arrayOf,
  shape,
  checkPropTypes,
} from 'prop-types';
import { Button, Tooltip } from '@patternfly/react-core';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import AlertModal from '../AlertModal';

const requireNameOrUsername = props => {
  const { name, username } = props;
  if (!name && !username) {
    return new Error(
      `One of 'name' or 'username' is required by ItemToDelete component.`
    );
  }
  if (name) {
    checkPropTypes(
      {
        name: string,
      },
      { name: props.name },
      'prop',
      'ItemToDelete'
    );
  }
  if (username) {
    checkPropTypes(
      {
        username: string,
      },
      { username: props.username },
      'prop',
      'ItemToDelete'
    );
  }
  return null;
};

const ItemToDelete = shape({
  id: number.isRequired,
  name: requireNameOrUsername,
  username: requireNameOrUsername,
  summary_fields: shape({
    user_capabilities: shape({
      delete: bool.isRequired,
    }).isRequired,
  }).isRequired,
});

function cannotDelete(item) {
  return !item.summary_fields.user_capabilities.delete;
}

class ToolbarDeleteButton extends React.Component {
  static propTypes = {
    onDelete: func.isRequired,
    itemsToDelete: arrayOf(ItemToDelete).isRequired,
    pluralizedItemName: string,
  };

  static defaultProps = {
    pluralizedItemName: 'Items',
  };

  constructor(props) {
    super(props);

    this.state = {
      isModalOpen: false,
    };

    this.handleConfirmDelete = this.handleConfirmDelete.bind(this);
    this.handleCancelDelete = this.handleCancelDelete.bind(this);
    this.handleDelete = this.handleDelete.bind(this);
  }

  handleConfirmDelete() {
    this.setState({ isModalOpen: true });
  }

  handleCancelDelete() {
    this.setState({ isModalOpen: false });
  }

  handleDelete() {
    const { onDelete } = this.props;
    onDelete();
    this.setState({ isModalOpen: false });
  }

  renderTooltip() {
    const { itemsToDelete, pluralizedItemName, i18n } = this.props;

    const itemsUnableToDelete = itemsToDelete
      .filter(cannotDelete)
      .map(item => item.name)
      .join(', ');
    if (itemsToDelete.some(cannotDelete)) {
      return (
        <div>
          {i18n._(
            t`You do not have permission to delete the following ${pluralizedItemName}: ${itemsUnableToDelete}`
          )}
        </div>
      );
    }
    if (itemsToDelete.length) {
      return i18n._(t`Delete`);
    }
    return i18n._(t`Select a row to delete`);
  }

  render() {
    const { itemsToDelete, pluralizedItemName, i18n } = this.props;
    const { isModalOpen } = this.state;
    const modalTitle = i18n._(t`Delete ${pluralizedItemName}?`);

    const isDisabled =
      itemsToDelete.length === 0 || itemsToDelete.some(cannotDelete);

    // NOTE: Once PF supports tooltips on disabled elements,
    // we can delete the extra <div> around the <DeleteButton> below.
    // See: https://github.com/patternfly/patternfly-react/issues/1894
    return (
      <Fragment>
        <Tooltip content={this.renderTooltip()} position="top">
          <div>
            <Button
              variant="danger"
              aria-label={i18n._(t`Delete`)}
              onClick={this.handleConfirmDelete}
              isDisabled={isDisabled}
            >
              {i18n._(t`Delete`)}
            </Button>
          </div>
        </Tooltip>
        {isModalOpen && (
          <AlertModal
            variant="danger"
            title={modalTitle}
            isOpen={isModalOpen}
            onClose={this.handleCancelDelete}
            actions={[
              <Button
                key="delete"
                variant="danger"
                aria-label={i18n._(t`confirm delete`)}
                onClick={this.handleDelete}
              >
                {i18n._(t`Delete`)}
              </Button>,
              <Button
                key="cancel"
                variant="secondary"
                aria-label={i18n._(t`cancel delete`)}
                onClick={this.handleCancelDelete}
              >
                {i18n._(t`Cancel`)}
              </Button>,
            ]}
          >
            <div>{i18n._(t`This action will delete the following:`)}</div>
            {itemsToDelete.map(item => (
              <span key={item.id}>
                <strong>{item.name || item.username}</strong>
                <br />
              </span>
            ))}
          </AlertModal>
        )}
      </Fragment>
    );
  }
}

export default withI18n()(ToolbarDeleteButton);
