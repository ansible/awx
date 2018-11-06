import React from 'react';
import { mount } from 'enzyme';
import About from '../../src/components/About';

let aboutWrapper;
let headerElem;

describe('<About />', () => {
  test('initially renders without crashing', () => {
    aboutWrapper = mount(<About />);
    headerElem = aboutWrapper.find('h2');
    expect(aboutWrapper.length).toBe(1);
    expect(headerElem.length).toBe(1);
  });
});
