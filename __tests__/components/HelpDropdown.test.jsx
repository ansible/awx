import React from 'react';
import { mount } from 'enzyme';
import { I18nProvider } from '@lingui/react';
import HelpDropdown from '../../src/components/HelpDropdown';

let questionCircleIcon;
let dropdownWrapper;
let dropdownComponentInstance;
let dropdownToggle;
let dropdownItems;
let dropdownItem;

beforeEach(() => {
  dropdownWrapper = mount(
    <I18nProvider>
      <HelpDropdown />
    </I18nProvider>
  );
  dropdownComponentInstance = dropdownWrapper.find(HelpDropdown).instance();
});

afterEach(() => {
  dropdownWrapper.unmount();
});

describe('<HelpDropdown />', () => {
  test('initially renders without crashing', () => {
    expect(dropdownWrapper.length).toBe(1);
    expect(dropdownComponentInstance.state.isOpen).toEqual(false);
    expect(dropdownComponentInstance.state.showAboutModal).toEqual(false);
    questionCircleIcon = dropdownWrapper.find('QuestionCircleIcon');
    expect(questionCircleIcon.length).toBe(1);
  });

  test('renders two dropdown items', () => {
    dropdownComponentInstance.setState({ isOpen: true });
    dropdownWrapper.update();
    dropdownItems = dropdownWrapper.find('DropdownItem');
    expect(dropdownItems.length).toBe(2);
    const dropdownTexts = dropdownItems.map(item => item.text());
    expect(dropdownTexts).toEqual(['Help', 'About']);
  });

  test('onToggle sets state.isOpen to opposite', () => {
    dropdownComponentInstance.setState({ isOpen: true });
    dropdownWrapper.update();
    dropdownToggle = dropdownWrapper.find('DropdownToggle > DropdownToggle');
    dropdownToggle.simulate('click');
    expect(dropdownComponentInstance.state.isOpen).toEqual(false);
  });

  test('about dropdown item sets state.showAboutModal to true', () => {
    dropdownComponentInstance.setState({ isOpen: true });
    dropdownWrapper.update();
    dropdownItem = dropdownWrapper.find('DropdownItem a').at(1);
    dropdownItem.simulate('click');
    expect(dropdownComponentInstance.state.showAboutModal).toEqual(true);
  });

  test('onAboutModalClose sets state.showAboutModal to false', () => {
    dropdownComponentInstance.setState({ showAboutModal: true });
    dropdownWrapper.update();
    const aboutModal = dropdownWrapper.find('AboutModal');
    aboutModal.find('AboutModalBoxCloseButton Button').simulate('click');
    expect(dropdownComponentInstance.state.showAboutModal).toEqual(false);
  });
});

