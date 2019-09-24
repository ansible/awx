import React, { Fragment } from 'react';
import { func, bool, number, string, arrayOf, shape } from 'prop-types';
import { Button, Tooltip } from '@patternfly/react-core';
import { TrashAltIcon } from '@patternfly/react-icons';
import styled from 'styled-components';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import AlertModal from '../AlertModal';

const DeleteButton = styled(Button)`
  padding: 5px 8px;

  &:hover {
    background-color: #d9534f;
    color: white;
  }

  &[disabled] {
    color: var(--pf-c-button--m-plain--Color);
    pointer-events: initial;
    cursor: not-allowed;
  }
`;

const ItemToDelete = shape({
  id: number.isRequired,
  name: string.isRequired,
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

    const isDisabled =
      itemsToDelete.length === 0 || itemsToDelete.some(cannotDelete);

    // NOTE: Once PF supports tooltips on disabled elements,
    // we can delete the extra <div> around the <DeleteButton> below.
    // See: https://github.com/patternfly/patternfly-react/issues/1894
    return (
      <Fragment>
        <Tooltip content={this.renderTooltip()} position="top">
          <div>
            <DeleteButton
              variant="plain"
              aria-label={i18n._(t`Delete`)}
              onClick={this.handleConfirmDelete}
              isDisabled={isDisabled}
            >
              <TrashAltIcon />
            </DeleteButton>
          </div>
        </Tooltip>
        {isModalOpen && (
          <AlertModal
            variant="danger"
            title={pluralizedItemName}
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
            {i18n._(t`Are you sure you want to delete:`)}
            <br />
            {itemsToDelete.map(item => (
              <span key={item.id}>
                <strong>{item.name}</strong>
                <br />
              </span>
            ))}
            <br />
          </AlertModal>
        )}
      </Fragment>
    );
  }
}

export default withI18n()(ToolbarDeleteButton);
