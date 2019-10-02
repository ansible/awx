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
    value: arrayOf(Item).isRequired,
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
      isExpanded: false,
    };
    this.handleKeyDown = this.handleKeyDown.bind(this);
    this.handleInputChange = this.handleInputChange.bind(this);
    this.removeItem = this.removeItem.bind(this);
    this.handleClick = this.handleClick.bind(this);
    this.createNewItem = this.createNewItem.bind(this);
  }

  componentDidMount() {
    document.addEventListener('mousedown', this.handleClick, false);
  }

  componentWillUnmount() {
    document.removeEventListener('mousedown', this.handleClick, false);
  }

  handleClick(e, option) {
    if (this.node && this.node.contains(e.target)) {
      if (option) {
        e.preventDefault();
        this.addItem(option);
      }
    } else {
      this.setState({ input: '', isExpanded: false });
    }
  }

  addItem(item) {
    const { value, onAddNewItem, onChange } = this.props;
    const items = value.concat(item);
    onAddNewItem(item);
    onChange(items);
    this.close();
  }

  // TODO: UpArrow & DownArrow for menu navigation
  handleKeyDown(event) {
    const { value, options } = this.props;
    const { input } = this.state;
    if (event.key === 'Tab') {
      this.close();
      return;
    }
    if (!input || event.key !== 'Enter') {
      return;
    }

    const isAlreadySelected = value.some(i => i.name === input);
    if (isAlreadySelected) {
      event.preventDefault();
      this.close();
      return;
    }

    const match = options.find(item => item.name === input);
    const isNewItem = !match || !value.find(item => item.id === match.id);
    if (isNewItem) {
      event.preventDefault();
      this.addItem(match || this.createNewItem(input));
    }
  }

  close() {
    this.setState({
      isExpanded: false,
      input: '',
    });
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

  handleInputChange(value) {
    this.setState({ input: value, isExpanded: true });
  }

  removeItem(item) {
    const { value, onRemoveItem, onChange } = this.props;
    const remainingItems = value.filter(chip => chip.id !== item.id);

    onRemoveItem(item);
    onChange(remainingItems);
  }

  render() {
    const { value, options } = this.props;
    const { input, isExpanded } = this.state;

    const dropdownOptions = options.map(option => (
      <Fragment key={option.id}>
        {option.name.includes(input) ? (
          <DropdownItem
            component="button"
            isDisabled={value.some(item => item.id === option.id)}
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
              onFocus={() => this.setState({ isExpanded: true })}
              onChange={this.handleInputChange}
              onKeyDown={this.handleKeyDown}
            />
            <Dropdown
              type="button"
              isPlain
              value={value}
              toggle={<DropdownToggle isPlain>Labels</DropdownToggle>}
              // Above is not visible but is a required prop from Patternfly
              isOpen={isExpanded}
              dropdownItems={dropdownOptions}
            />
          </div>
          <div css="margin: 10px">
            <ChipGroup>
              {value.map(item => (
                <Chip
                  key={item.id}
                  onClick={() => {
                    this.removeItem(item);
                  }}
                >
                  {item.name}
                </Chip>
              ))}
            </ChipGroup>
          </div>
        </InputGroup>
      </Fragment>
    );
  }
}
export default MultiSelect;
