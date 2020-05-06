import React from 'react';
import { mountWithContexts } from '../../../../../../testUtils/enzymeHelpers';
import RunStep from './RunStep';

let wrapper;
const linkType = 'always';
const onUpdateLinkType = jest.fn();

describe('RunStep', () => {
  beforeAll(() => {
    wrapper = mountWithContexts(
      <RunStep linkType={linkType} onUpdateLinkType={onUpdateLinkType} />
    );
  });

  afterAll(() => {
    wrapper.unmount();
  });

  test('Default selected card matches default link type when present', () => {
    expect(wrapper.find('#link-type-success').props().isSelected).toBe(false);
    expect(wrapper.find('#link-type-failure').props().isSelected).toBe(false);
    expect(wrapper.find('#link-type-always').props().isSelected).toBe(true);
  });

  test('Clicking success card makes expected callback', () => {
    wrapper.find('#link-type-success').simulate('click');
    expect(onUpdateLinkType).toHaveBeenCalledWith('success');
  });

  test('Clicking failure card makes expected callback', () => {
    wrapper.find('#link-type-failure').simulate('click');
    expect(onUpdateLinkType).toHaveBeenCalledWith('failure');
  });

  test('Clicking always card makes expected callback', () => {
    wrapper.find('#link-type-always').simulate('click');
    expect(onUpdateLinkType).toHaveBeenCalledWith('always');
  });
});
