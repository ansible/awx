import React from 'react';
import { mount } from 'enzyme';
import HelpDropdown from '../../src/components/HelpDropdown';

let questionCircleIcon;
let dropdownWrapper;
let dropdownToggle;
let dropdownItems;
let dropdownItem;

beforeEach(() => {
  dropdownWrapper = mount(<HelpDropdown />);
});

afterEach(() => {
  dropdownWrapper.unmount();
});

describe('<HelpDropdown />', () => {
  test('initially renders without crashing', () => {
    expect(dropdownWrapper.length).toBe(1);
    expect(dropdownWrapper.state('isOpen')).toEqual(false);
    expect(dropdownWrapper.state('showAboutModal')).toEqual(false);
    questionCircleIcon = dropdownWrapper.find('QuestionCircleIcon');
    expect(questionCircleIcon.length).toBe(1);
  });

  test('renders two dropdown items', () => {
    dropdownWrapper.setState({ isOpen: true });
    dropdownItems = dropdownWrapper.find('DropdownItem');
    expect(dropdownItems.length).toBe(2);
    const dropdownTexts = dropdownItems.map(item => item.text());
    expect(dropdownTexts).toEqual(['Help', 'About']);
  });

  test('onToggle sets state.isOpen to opposite', () => {
    dropdownWrapper.setState({ isOpen: true });
    dropdownToggle = dropdownWrapper.find('DropdownToggle > DropdownToggle');
    dropdownToggle.simulate('click');
    expect(dropdownWrapper.state('isOpen')).toEqual(false);
  });

  test('about dropdown item sets state.showAboutModal to true', () => {
    dropdownWrapper.setState({ isOpen: true });
    dropdownItem = dropdownWrapper.find('DropdownItem a').at(1);
    dropdownItem.simulate('click');
    expect(dropdownWrapper.state('showAboutModal')).toEqual(true);
  });

  test('onAboutModalClose sets state.showAboutModal to false', () => {
    dropdownWrapper.setState({ showAboutModal: true });
    const aboutModal = dropdownWrapper.find('AboutModal');
    aboutModal.find('AboutModalBoxCloseButton Button').simulate('click');
    expect(dropdownWrapper.state('showAboutModal')).toEqual(false);
  });
});

