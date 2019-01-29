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
import { t } from '@lingui/macro';

import CheckboxListItem from '../ListItem';

import SelectedList from '../SelectedList';

class Lookup extends React.Component {
  constructor (props) {
    super(props);
    this.state = {
      isModalOpen: false,
    };
    this.handleModalToggle = this.handleModalToggle.bind(this);
    this.onLookup = this.onLookup.bind(this);
    this.onChecked = this.onChecked.bind(this);
    this.wrapTags = this.wrapTags.bind(this);
    this.onRemove = this.onRemove.bind(this);
  }

  onLookup () {
    this.handleModalToggle();
  }

  onChecked (row) {
    const { lookupChange } = this.props;
    lookupChange(row);
  }

  onRemove (evt) {
    const { lookupChange } = this.props;
    lookupChange(evt.target.id);
  }

  handleModalToggle () {
    this.setState((prevState) => ({
      isModalOpen: !prevState.isModalOpen,
    }));
  }

  wrapTags (tags) {
    return tags.filter(tag => tag.isChecked).map((tag) => (
      <span className="awx-c-tag--pill" key={tag.id}>
        {tag.name}
        <Button className="awx-c-icon--remove" id={tag.id} onClick={this.onRemove}>
          x
        </Button>
      </span>
    ));
  }

  render () {
    const { isModalOpen } = this.state;
    const { data, lookupHeader, selected } = this.props;
    return (
      <div className="pf-c-input-group awx-lookup">
        <Button className="pf-c-input-group__text" aria-label="search" id="search" onClick={this.onLookup}>
          <SearchIcon />
        </Button>
        <div className="pf-c-form-control">{this.wrapTags(data)}</div>
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
                isSelected={i.isChecked}
                onSelect={() => this.onChecked(i)}
              />
            ))}
          </ul>
          {selected.length > 0 && (
            <I18n>
              {({ i18n }) => (
                <SelectedList
                  label={i18n._(t`Selected`)}
                  selected={selected}
                  showOverflowAfter={5}
                  onRemove={this.onChecked}
                />
              )}
            </I18n>
          )}
          <ActionGroup className="at-align-right">
            <Toolbar>
              <ToolbarGroup>
                <Button className="at-C-SubmitButton" variant="primary" onClick={this.handleModalToggle}>Select</Button>
              </ToolbarGroup>
              <ToolbarGroup>
                <Button className="at-C-CancelButton" variant="secondary" onClick={this.handleModalToggle}>Cancel</Button>
              </ToolbarGroup>
            </Toolbar>
          </ActionGroup>
        </Modal>
      </div>
    );
  }
}
export default Lookup;
