import React from 'react';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import PageControls from './PageControls';

let wrapper;
let AngleDoubleUpIcon;
let AngleDoubleDownIcon;
let AngleUpIcon;
let AngleDownIcon;

const findChildren = () => {
  AngleDoubleUpIcon = wrapper.find('AngleDoubleUpIcon');
  AngleDoubleDownIcon = wrapper.find('AngleDoubleDownIcon');
  AngleUpIcon = wrapper.find('AngleUpIcon');
  AngleDownIcon = wrapper.find('AngleDownIcon');
};

describe('PageControls', () => {
  test('should render successfully', () => {
    wrapper = mountWithContexts(<PageControls />);
    expect(wrapper).toHaveLength(1);
  });

  test('should render menu control icons', () => {
    wrapper = mountWithContexts(<PageControls />);
    findChildren();
    expect(AngleDoubleUpIcon.length).toBe(1);
    expect(AngleDoubleDownIcon.length).toBe(1);
    expect(AngleUpIcon.length).toBe(1);
    expect(AngleDownIcon.length).toBe(1);
  });
});
