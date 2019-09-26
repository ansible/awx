import React, { Component, Fragment } from 'react';
import { shape, number, string, func, arrayOf, oneOfType } from 'prop-types';
import { Chip, ChipGroup } from '@components/Chip';
import {
  Dropdown as PFDropdown,
  DropdownItem,
  TextInput as PFTextInput,
  DropdownToggle,
} from '@patternfly/react-core';
import styled from 'styled-components';

const InputGroup = styled.div`
  border: 1px solid black;
  margin-top: 2px;
`;

const TextInput = styled(PFTextInput)`
  border: none;
  width: 100%;
  padding-left: 8px;
`;

const Dropdown = styled(PFDropdown)`
  width: 100%;
  .pf-c-dropdown__toggle.pf-m-plain {
    display: none;
  }
  display: block;
  .pf-c-dropdown__menu {
    max-height: 200px;
    overflow: scroll;
  }
  && button[disabled] {
    color: var(--pf-c-button--m-plain--Color);
    pointer-events: initial;
    cursor: not-allowed;
    color: var(--pf-global--disabled-color--200);
  }
`;

const Item = shape({
  id: oneOfType([number, string]).isRequired,
  name: string.isRequired,
});

class MultiSelect extends Component {
  static propTypes = {
    associatedItems: arrayOf(Item).isRequired,
    options: arrayOf(Item),
    onAddNewItem: func,
    onRemoveItem: func,
    onChange: func,
    createNewItem: func,
  };

  static defaultProps = {
    onAddNewItem: () => {},
    onRemoveItem: () => {},
    onChange: () => {},
    options: [],
    createNewItem: null,
  };

  constructor(props) {
    super(props);
    this.state = {
      input: '',
      chipItems: this.getInitialChipItems(),
      isExpanded: false,
    };
    this.handleAddItem = this.handleAddItem.bind(this);
    this.handleInputChange = this.handleInputChange.bind(this);
    this.handleSelection = this.handleSelection.bind(this);
    this.removeChip = this.removeChip.bind(this);
    this.handleClick = this.handleClick.bind(this);
    this.createNewItem = this.createNewItem.bind(this);
  }

  componentDidMount() {
    document.addEventListener('mousedown', this.handleClick, false);
  }

  componentWillUnmount() {
    document.removeEventListener('mousedown', this.handleClick, false);
  }

  getInitialChipItems() {
    const { associatedItems } = this.props;
    return associatedItems.map(item => ({ ...item }));
  }

  handleClick(e, option) {
    if (this.node && this.node.contains(e.target)) {
      if (option) {
        this.handleSelection(e, option);
      }
    } else {
      this.setState({ input: '', isExpanded: false });
    }
  }

  handleSelection(e, item) {
    const { chipItems } = this.state;
    const { onAddNewItem, onChange } = this.props;
    e.preventDefault();

    const items = chipItems.concat({ name: item.name, id: item.id });
    this.setState({
      chipItems: items,
      isExpanded: false,
    });
    onAddNewItem(item);
    onChange(items);
  }

  createNewItem(name) {
    const { createNewItem } = this.props;
    if (createNewItem) {
      return createNewItem(name);
    }
    return {
      id: Math.random(),
      name,
    };
  }

  handleAddItem(event) {
    const { input, chipItems } = this.state;
    const { options, onAddNewItem, onChange } = this.props;
    const match = options.find(item => item.name === input);
    const isIncluded = chipItems.some(chipItem => chipItem.name === input);

    if (!input) {
      return;
    }

    if (isIncluded) {
      // This event.preventDefault prevents the form from submitting
      // if the user tries to create 2 chips of the same name
      event.preventDefault();
      this.setState({ input: '', isExpanded: false });
      return;
    }
    const isNewItem = !match || !chipItems.find(item => item.id === match.id);
    if (event.key === 'Enter' && isNewItem) {
      event.preventDefault();
      const newItem = match || this.createNewItem(input);
      const items = chipItems.concat(newItem);
      this.setState({
        chipItems: items,
        isExpanded: false,
        input: '',
      });
      onAddNewItem(newItem);
      onChange(items);
    } else if (!isNewItem || event.key === 'Tab') {
      this.setState({ isExpanded: false, input: '' });
    }
  }

  handleInputChange(value) {
    this.setState({ input: value, isExpanded: true });
  }

  removeChip(e, item) {
    const { onRemoveItem, onChange } = this.props;
    const { chipItems } = this.state;
    const chips = chipItems.filter(chip => chip.id !== item.id);

    this.setState({ chipItems: chips });
    onRemoveItem(item);
    onChange(chips);

    e.preventDefault();
  }

  render() {
    const { options } = this.props;
    const { chipItems, input, isExpanded } = this.state;

    const list = options.map(option => (
      <Fragment key={option.id}>
        {option.name.includes(input) ? (
          <DropdownItem
            component="button"
            isDisabled={chipItems.some(item => item.id === option.id)}
            value={option.name}
            onClick={e => {
              this.handleClick(e, option);
            }}
          >
            {option.name}
          </DropdownItem>
        ) : null}
      </Fragment>
    ));

    const chips = (
      <ChipGroup>
        {chipItems &&
          chipItems.map(item => (
            <Chip
              key={item.id}
              onClick={e => {
                this.removeChip(e, item);
              }}
            >
              {item.name}
            </Chip>
          ))}
      </ChipGroup>
    );
    return (
      <Fragment>
        <InputGroup>
          <div
            ref={node => {
              this.node = node;
            }}
          >
            <TextInput
              type="text"
              aria-label="labels"
              value={input}
              onClick={() => this.setState({ isExpanded: true })}
              onChange={this.handleInputChange}
              onKeyDown={this.handleAddItem}
            />
            <Dropdown
              type="button"
              isPlain
              value={chipItems}
              toggle={<DropdownToggle isPlain>Labels</DropdownToggle>}
              // Above is not rendered but is a required prop from Patternfly
              isOpen={isExpanded}
              dropdownItems={list}
            />
          </div>
          <div css="margin: 10px">{chips}</div>
        </InputGroup>
      </Fragment>
    );
  }
}
export default MultiSelect;
