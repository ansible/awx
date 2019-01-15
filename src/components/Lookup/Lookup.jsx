import React from 'react';

import { SearchIcon } from '@patternfly/react-icons';
import {
  Modal,
  Button,
  ActionGroup,
  Toolbar,
  ToolbarGroup,
} from '@patternfly/react-core';

import CheckboxListItem from '../ListItem'

class Lookup extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      isModalOpen: false,
    }
    this.handleModalToggle = this.handleModalToggle.bind(this);
    this.onLookup = this.onLookup.bind(this);
    this.onChecked = this.onChecked.bind(this);
    this.wrapTags = this.wrapTags.bind(this);
    this.onRemove = this.onRemove.bind(this);
  }

  handleModalToggle() {
    this.setState((prevState, _) => ({
      isModalOpen: !prevState.isModalOpen,
    }));
  };

  onLookup() {
    this.handleModalToggle();
  }

  onChecked(_, evt) {
    this.props.lookupChange(evt.target.value);
  };

  onRemove(evt) {
    this.props.lookupChange(evt.target.id);
  }
  wrapTags(tags) {
    return tags.filter(tag => tag.isChecked).map((tag, index) => {
      return (
        <span className="awx-c-tag--pill" key={index}>{tag.name}<span className="awx-c-icon--remove" id={tag.id} onClick={this.onRemove}>x</span></span>
      )
    })
  }

  render() {
    const { isModalOpen } = this.state;
    const { data } = this.props;
    return (
      <div className="pf-c-input-group awx-lookup">
        <span className="pf-c-input-group__text" aria-label="search" id="search" onClick={this.onLookup}><SearchIcon /></span>
        <div className="pf-c-form-control">{this.wrapTags(this.props.data)}</div>
        <Modal
          className="awx-c-modal"
          title={`Select ${this.props.lookup_header}`}
          isOpen={isModalOpen}
          onClose={this.handleModalToggle}
        >
          <ul className="pf-c-data-list awx-c-list">
            {data.map(i =>
              <CheckboxListItem
                key={i.id}
                itemId={i.id}
                name={i.name}
                isSelected={i.isChecked}
                onSelect={this.onChecked}
              />
            )}
          </ul>
          <ActionGroup className="at-align-right">
            <Toolbar>
              <ToolbarGroup>
                <Button className="at-C-SubmitButton" variant="primary" onClick={this.handleModalToggle} >Select</Button>
              </ToolbarGroup>
              <ToolbarGroup>
                <Button className="at-C-CancelButton" variant="secondary" onClick={this.handleModalToggle}>Cancel</Button>
              </ToolbarGroup>
            </Toolbar>
          </ActionGroup>
        </Modal>
      </div>
    )
  }
}
export default Lookup;
