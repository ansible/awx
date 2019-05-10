import React, { Fragment } from 'react';
import { func, bool, number, string, arrayOf, shape } from 'prop-types';
import { Button as PFButton, Tooltip } from '@patternfly/react-core';
import { TrashAltIcon } from '@patternfly/react-icons';
import { I18n, i18nMark } from '@lingui/react';
import { Trans, t } from '@lingui/macro';
import styled from 'styled-components';
import AlertModal from '../AlertModal';
import { pluralize } from '../../util/strings';

const Button = styled(PFButton)`
  width: 30px;
  height: 30px;
  display: flex;
  justify-content: center;
  margin-right: 20px;
  border-radius: 3px;


  &:disabled {
    cursor: not-allowed;
    &:hover {
      background-color: white;

      > svg {
        color: #d2d2d2;
      }
    }
  }

  &:hover {
    background-color:#d9534f;
    > svg {
      color: white;
    }
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

function cannotDelete (item) {
  return !item.summary_fields.user_capabilities.delete;
}

class ToolbarDeleteButton extends React.Component {
  static propTypes = {
    onDelete: func.isRequired,
    itemsToDelete: arrayOf(ItemToDelete).isRequired,
    itemName: string,
  };

  static defaultProps = {
    itemName: 'item',
  };

  constructor (props) {
    super(props);

    this.state = {
      isModalOpen: false,
    };

    this.handleConfirmDelete = this.handleConfirmDelete.bind(this);
    this.handleCancelDelete = this.handleCancelDelete.bind(this);
    this.handleDelete = this.handleDelete.bind(this);
  }

  handleConfirmDelete () {
    this.setState({ isModalOpen: true });
  }

  handleCancelDelete () {
    this.setState({ isModalOpen: false, });
  }

  handleDelete () {
    const { onDelete } = this.props;
    onDelete();
    this.setState({ isModalOpen: false });
  }

  renderTooltip () {
    const { itemsToDelete, itemName } = this.props;
    if (itemsToDelete.some(cannotDelete)) {
      return (
        <div>
          <Trans>
            You dont have permission to delete the following
            {' '}
            {pluralize(itemName)}
            :
          </Trans>
          {itemsToDelete
            .filter(cannotDelete)
            .map(item => (
              <div key={item.id}>
                {item.name}
              </div>
            ))
          }
        </div>
      );
    }
    if (itemsToDelete.length) {
      return i18nMark('Delete');
    }
    return i18nMark('Select a row to delete');
  }

  render () {
    const { itemsToDelete, itemName } = this.props;
    const { isModalOpen } = this.state;

    const isDisabled = itemsToDelete.length === 0
      || itemsToDelete.some(cannotDelete);

    return (
      <I18n>
        {({ i18n }) => (
          <Fragment>
            <Tooltip
              content={this.renderTooltip()}
              position="left"
            >
              <Button
                variant="plain"
                aria-label={i18n._(t`Delete`)}
                onClick={this.handleConfirmDelete}
                isDisabled={isDisabled}
              >
                <TrashAltIcon />
              </Button>
            </Tooltip>
            { isModalOpen && (
              <AlertModal
                variant="danger"
                title={itemsToDelete === 1
                  ? i18n._(t`Delete ${itemName}`)
                  : i18n._(t`Delete ${pluralize(itemName)}`)
                }
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
                  </Button>
                ]}
              >
                {i18n._(t`Are you sure you want to delete:`)}
                <br />
                {itemsToDelete.map((item) => (
                  <span key={item.id}>
                    <strong>
                      {item.name}
                    </strong>
                    <br />
                  </span>
                ))}
                <br />
              </AlertModal>
            )}
          </Fragment>
        )}
      </I18n>
    );
  }
}

export default ToolbarDeleteButton;
