import React from 'react';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import CardCloseButton from './CardCloseButton';

describe('<CardCloseButton>', () => {
  test('should render close button', () => {
    const wrapper = mountWithContexts(<CardCloseButton />);
    const button = wrapper.find('Button');
    expect(button).toHaveLength(1);
    expect(button.prop('variant')).toBe('plain');
    expect(button.prop('aria-label')).toBe('Close');
    expect(wrapper.find('Link')).toHaveLength(0);
  });

  test('should render close link when `linkTo` prop provided', () => {
    const wrapper = mountWithContexts(<CardCloseButton linkTo="/foo" />);
    expect(wrapper.find('Button')).toHaveLength(0);
    const link = wrapper.find('Link');
    expect(link).toHaveLength(1);
    expect(link.prop('to')).toEqual('/foo');
    expect(link.prop('aria-label')).toEqual('Close');
  });
});
