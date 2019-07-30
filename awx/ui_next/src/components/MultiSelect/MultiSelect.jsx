import React, { Component, Fragment } from 'react';
import PropTypes from 'prop-types';
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

class MultiSelect extends Component {
  static propTypes = {
    associatedItems: PropTypes.arrayOf(
      PropTypes.shape({
        name: PropTypes.string.isRequired,
      })
    ).isRequired,
    onAddNewItem: PropTypes.func.isRequired,
    onRemoveItem: PropTypes.func.isRequired,
  };

  constructor(props) {
    super(props);
    this.myRef = React.createRef();
    this.state = {
      input: '',
      chipItems: [],
      isExpanded: false,
    };
    this.handleAddItem = this.handleAddItem.bind(this);
    this.handleInputChange = this.handleInputChange.bind(this);
    this.handleSelection = this.handleSelection.bind(this);
    this.removeChip = this.removeChip.bind(this);
    this.handleClick = this.handleClick.bind(this);
  }

  componentDidMount() {
    this.renderChips();
    document.addEventListener('mousedown', this.handleClick, false);
  }

  handleClick(e, option) {
    if (this.node && this.node.contains(e.target)) {
      if (option) {
        this.handleSelection(e, option);
      }
      this.setState({ isExpanded: true });
    } else {
      this.setState({ isExpanded: false });
    }
  }

  renderChips() {
    const { associatedItems } = this.props;
    const items = associatedItems.map(item => ({
      name: item.name,
      id: item.id,
      organization: item.organization,
    }));
    this.setState({
      chipItems: items,
    });
  }

  handleSelection(e, item) {
    const { chipItems } = this.state;
    const { onAddNewItem } = this.props;

    this.setState({
      chipItems: chipItems.concat({ name: item.name, id: item.id }),
    });
    onAddNewItem(item);
    e.preventDefault();
  }

  handleAddItem(event) {
    const { input, chipItems } = this.state;
    const { onAddNewItem } = this.props;
    const newChip = { name: input, id: Math.random() };
    if (event.key === 'Tab') {
      this.setState({
        chipItems: chipItems.concat(newChip),
        isExpanded: false,
        input: '',
      });

      onAddNewItem(input);
    }
  }

  handleInputChange(e) {
    this.setState({ input: e, isExpanded: true });
  }

  removeChip(e, item) {
    const { onRemoveItem } = this.props;
    const { chipItems } = this.state;
    const chips = chipItems.filter(chip => chip.name !== item.name);

    this.setState({ chipItems: chips });
    onRemoveItem(item);

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
