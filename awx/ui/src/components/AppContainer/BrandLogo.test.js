import React from 'react';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import BrandLogo from './BrandLogo';

let logoWrapper;
let brandLogoElem;
let imgElem;

const findChildren = () => {
  brandLogoElem = logoWrapper.find('BrandLogo');
  imgElem = logoWrapper.find('img');
};

describe('<BrandLogo />', () => {
  test('initially renders without crashing', () => {
    logoWrapper = mountWithContexts(<BrandLogo />);
    findChildren();
    expect(logoWrapper.length).toBe(1);
    expect(brandLogoElem.length).toBe(1);
    expect(imgElem.length).toBe(1);
  });
});
