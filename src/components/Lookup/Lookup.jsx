import React from 'react';

import { SearchIcon } from '@patternfly/react-icons';
import {
  Modal,
  Button,
  ActionGroup,
  Toolbar,
  ToolbarGroup,
} from '@patternfly/react-core';
import { I18n } from '@lingui/react';
import { t, Trans } from '@lingui/macro';

import CheckboxListItem from '../ListItem';

import SelectedList from '../SelectedList';

class Lookup extends React.Component {
  constructor (props) {
    super(props);
    this.state = {
      isModalOpen: false,
      lookupSelectedItems: []
    };
    this.handleModalToggle = this.handleModalToggle.bind(this);
    this.wrapTags = this.wrapTags.bind(this);
    this.toggleSelected = this.toggleSelected.bind(this);
    this.saveModal = this.saveModal.bind(this);
  }

  toggleSelected (row) {
    const { lookupSelectedItems } = this.state;
    const selectedIndex = lookupSelectedItems
      .findIndex(selectedRow => selectedRow.id === row.id);
    if (selectedIndex > -1) {
      lookupSelectedItems.splice(selectedIndex, 1);
      this.setState({ lookupSelectedItems });
    } else {
      this.setState(prevState => ({
        lookupSelectedItems: [...prevState.lookupSelectedItems, row]
      }));
    }
  }

  handleModalToggle () {
    const { isModalOpen } = this.state;
    const { selected } = this.props;
    // Resets the selected items from parent state whenever modal is opened
    // This handles the case where the user closes/cancels the modal and
    // opens it again
    if (!isModalOpen) {
      this.setState({ lookupSelectedItems: [...selected] });
    }
    this.setState((prevState) => ({
      isModalOpen: !prevState.isModalOpen,
    }));
  }

  saveModal () {
    const { onLookupSave } = this.props;
    const { lookupSelectedItems } = this.state;
    onLookupSave(lookupSelectedItems);
    this.handleModalToggle();
  }

  wrapTags (tags) {
    return tags.map(tag => (
      <span className="awx-c-tag--pill" key={tag.id}>
        {tag.name}
        <Button className="awx-c-icon--remove" id={tag.id} onClick={() => this.toggleSelected(tag)}>
          x
        </Button>
      </span>
    ));
  }

  render () {
    const { isModalOpen, lookupSelectedItems } = this.state;
    const { data, lookupHeader, selected } = this.props;
    return (
      <div className="pf-c-input-group awx-lookup">
        <Button className="pf-c-input-group__text" aria-label="search" id="search" onClick={this.handleModalToggle}>
          <SearchIcon />
        </Button>
        <div className="pf-c-form-control">{this.wrapTags(selected)}</div>
        <Modal
          className="awx-c-modal"
          title={`Select ${lookupHeader}`}
          isOpen={isModalOpen}
          onClose={this.handleModalToggle}
        >
          <ul className="pf-c-data-list awx-c-list">
            {data.map(i => (
              <CheckboxListItem
                key={i.id}
                itemId={i.id}
                name={i.name}
                isSelected={lookupSelectedItems.some(item => item.id === i.id)}
                onSelect={() => this.toggleSelected(i)}
              />
            ))}
          </ul>
          {lookupSelectedItems.length > 0 && (
            <I18n>
              {({ i18n }) => (
                <SelectedList
                  label={i18n._(t`Selected`)}
                  selected={lookupSelectedItems}
                  showOverflowAfter={5}
                  onRemove={this.toggleSelected}
                />
              )}
            </I18n>
          )}
          <ActionGroup className="at-align-right">
            <Toolbar>
              <ToolbarGroup>
                <Button className="at-C-SubmitButton" variant="primary" onClick={this.saveModal}>
                  <Trans>Select</Trans>
                </Button>
              </ToolbarGroup>
              <ToolbarGroup>
                <Button className="at-C-CancelButton" variant="secondary" onClick={this.handleModalToggle}>
                  <Trans>Cancel</Trans>
                </Button>
              </ToolbarGroup>
            </Toolbar>
          </ActionGroup>
        </Modal>
      </div>
    );
  }
}
export default Lookup;
