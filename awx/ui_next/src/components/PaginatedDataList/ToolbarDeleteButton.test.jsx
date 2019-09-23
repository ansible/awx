import React from 'react';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import ToolbarDeleteButton from './ToolbarDeleteButton';

const itemA = {
  id: 1,
  name: 'Foo',
  summary_fields: { user_capabilities: { delete: true } },
};
const itemB = {
  id: 1,
  name: 'Foo',
  summary_fields: { user_capabilities: { delete: false } },
};

describe('<ToolbarDeleteButton />', () => {
  test('should render button', () => {
    const wrapper = mountWithContexts(
      <ToolbarDeleteButton onDelete={() => {}} itemsToDelete={[]} />
    );
    expect(wrapper.find('button')).toHaveLength(1);
    expect(wrapper.find('ToolbarDeleteButton')).toMatchSnapshot();
  });

  test('should open confirmation modal', () => {
    const wrapper = mountWithContexts(
      <ToolbarDeleteButton onDelete={() => {}} itemsToDelete={[itemA]} />
    );
    wrapper.find('button').simulate('click');
    expect(wrapper.find('ToolbarDeleteButton').state('isModalOpen')).toBe(true);
    wrapper.update();
    expect(wrapper.find('Modal')).toHaveLength(1);
  });

  test('should invoke onDelete prop', () => {
    const onDelete = jest.fn();
    const wrapper = mountWithContexts(
      <ToolbarDeleteButton onDelete={onDelete} itemsToDelete={[itemA]} />
    );
    wrapper.find('ToolbarDeleteButton').setState({ isModalOpen: true });
    wrapper.update();
    wrapper.find('button.pf-m-danger').simulate('click');
    expect(onDelete).toHaveBeenCalled();
    expect(wrapper.find('ToolbarDeleteButton').state('isModalOpen')).toBe(
      false
    );
  });

  test('should disable button when no delete permissions', () => {
    const wrapper = mountWithContexts(
      <ToolbarDeleteButton onDelete={() => {}} itemsToDelete={[itemB]} />
    );
    expect(wrapper.find('button[disabled]')).toHaveLength(1);
  });

  test('should render tooltip', () => {
    const wrapper = mountWithContexts(
      <ToolbarDeleteButton onDelete={() => {}} itemsToDelete={[itemA]} />
    );
    expect(wrapper.find('Tooltip')).toHaveLength(1);
    expect(wrapper.find('Tooltip').prop('content')).toEqual('Delete');
  });
});
