import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { mount } from 'enzyme';
import { I18nProvider } from '@lingui/react';
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
    logoWrapper = mount(
      <MemoryRouter>
        <I18nProvider>
          <TowerLogo />
        </I18nProvider>
      </MemoryRouter>
    );
    findChildren();
    expect(logoWrapper.length).toBe(1);
    expect(towerLogoElem.length).toBe(1);
    expect(brandElem.length).toBe(1);
  });

  test('adds navigation to route history on click', () => {
    logoWrapper = mount(
      <MemoryRouter>
        <I18nProvider>
          <TowerLogo linkTo="/" />
        </I18nProvider>
      </MemoryRouter>
    );
    findChildren();
    expect(towerLogoElem.props().history.length).toBe(1);
    logoWrapper.simulate('click');
    expect(towerLogoElem.props().history.length).toBe(2);
  });

  test('linkTo prop is optional', () => {
    logoWrapper = mount(
      <MemoryRouter>
        <I18nProvider>
          <TowerLogo />
        </I18nProvider>
      </MemoryRouter>
    );
    findChildren();
    expect(towerLogoElem.props().history.length).toBe(1);
    logoWrapper.simulate('click');
    expect(towerLogoElem.props().history.length).toBe(1);
  });

  test('handles mouse over and out state.hover changes', () => {
    logoWrapper = mount(
      <MemoryRouter>
        <I18nProvider>
          <TowerLogo />
        </I18nProvider>
      </MemoryRouter>
    );
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
