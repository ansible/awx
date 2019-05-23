import React from 'react';
import { mountWithContexts } from '../enzymeHelpers';
import TowerLogo from '../../src/components/TowerLogo';

let logoWrapper;
let towerLogoElem;
let svgElem;

const findChildren = () => {
  towerLogoElem = logoWrapper.find('TowerLogo');
  svgElem = logoWrapper.find('svg');
};

describe('<TowerLogo />', () => {
  test('initially renders without crashing', () => {
    logoWrapper = mountWithContexts(
      <TowerLogo />
    );
    findChildren();
    expect(logoWrapper.length).toBe(1);
    expect(towerLogoElem.length).toBe(1);
    expect(svgElem.length).toBe(1);
  });
});
