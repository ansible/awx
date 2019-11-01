import React from 'react';
import { mountWithContexts } from '@testUtils/enzymeHelpers';
import TemplateAddButton from './TemplateAddButton';

describe('<TemplateAddButton />', () => {
  test('should be closed initially', () => {
    const wrapper = mountWithContexts(<TemplateAddButton />);
    expect(wrapper.find('Dropdown').prop('isOpen')).toEqual(false);
  });

  test('should render two links', () => {
    const wrapper = mountWithContexts(<TemplateAddButton />);
    wrapper.find('button').simulate('click');
    expect(wrapper.find('Dropdown').prop('isOpen')).toEqual(true);
    expect(wrapper.find('Link')).toHaveLength(2);
  });

  test('should close when button re-clicked', () => {
    const wrapper = mountWithContexts(<TemplateAddButton />);
    wrapper.find('button').simulate('click');
    expect(wrapper.find('Dropdown').prop('isOpen')).toEqual(true);
    wrapper.find('button').simulate('click');
    expect(wrapper.find('Dropdown').prop('isOpen')).toEqual(false);
  });
});
