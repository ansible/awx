import React from 'react';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import BrandLogo from './BrandLogo';

let logoWrapper;
let brandLogoElem;
let svgElem;

const findChildren = () => {
  brandLogoElem = logoWrapper.find('BrandLogo');
  svgElem = logoWrapper.find('svg');
};

describe('<BrandLogo />', () => {
  test('initially renders without crashing', () => {
    logoWrapper = mountWithContexts(<BrandLogo />);
    findChildren();
    expect(logoWrapper.length).toBe(1);
    expect(brandLogoElem.length).toBe(1);
    expect(svgElem.length).toBe(1);
  });
});
