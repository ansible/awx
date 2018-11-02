import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { mount } from 'enzyme';
import TowerLogo from '../../src/components/TowerLogo';

let logoWrapper;
let towerLogoElem;
let brandElem;

const findChildren = () => {
  towerLogoElem = logoWrapper.find('TowerLogo');
  brandElem = logoWrapper.find('Brand');
};

describe('<TowerLogo />', () => {
  test('initially renders without crashing', () => {
    logoWrapper = mount(<MemoryRouter><TowerLogo /></MemoryRouter>);
    findChildren();
    expect(logoWrapper.length).toBe(1);
    expect(towerLogoElem.length).toBe(1);
    expect(brandElem.length).toBe(1);
  });

  test('adds navigation to route history on click', () => {
    const onLogoClick = jest.fn();
    logoWrapper = mount(<MemoryRouter><TowerLogo onClick={onLogoClick} /></MemoryRouter>);
    findChildren();
    expect(towerLogoElem.props().history.length).toBe(1);
    logoWrapper.simulate('click');
    expect(towerLogoElem.props().history.length).toBe(2);
  });

  test('gracefully handles not being passed click handler', () => {
    logoWrapper = mount(<MemoryRouter><TowerLogo /></MemoryRouter>);
    findChildren();
    expect(towerLogoElem.props().history.length).toBe(1);
    logoWrapper.simulate('click');
    expect(towerLogoElem.props().history.length).toBe(1);
  });

  test('handles mouse over and out state.hover changes', () => {
    const onLogoClick = jest.fn();
    logoWrapper = mount(<MemoryRouter><TowerLogo onClick={onLogoClick} /></MemoryRouter>);
    findChildren();
    findChildren();
    expect(brandElem.props().src).toBe('tower-logo-header.svg');
    brandElem.props().onMouseOver();
    expect(towerLogoElem.state().hover).toBe(true);
    logoWrapper.update();
    findChildren();
    expect(brandElem.props().src).toBe('tower-logo-header-hover.svg');
    brandElem.props().onMouseOut();
    expect(towerLogoElem.state().hover).toBe(false);
    logoWrapper.update();
    findChildren();
    expect(brandElem.props().src).toBe('tower-logo-header.svg');
  });
});
