import React from 'react';
import { mountWithContexts } from '@testUtils/enzymeHelpers';
import InventoryGroupForm from './InventoryGroupForm';

const group = {
  id: 1,
  name: 'Foo',
  description: 'Bar',
  variables: 'ying: false',
};
describe('<InventoryGroupForm />', () => {
  let wrapper;
  beforeEach(() => {
    wrapper = mountWithContexts(
      <InventoryGroupForm
        handleSubmit={jest.fn()}
        handleCancel={jest.fn()}
        group={group}
      />
    );
  });
  afterEach(() => {
    wrapper.unmount();
  });
  test('initially renders successfully', () => {
    expect(wrapper.length).toBe(1);
  });
  test('should render values for the fields that have them', () => {
    expect(wrapper.find("FormGroup[label='Name']").length).toBe(1);
    expect(wrapper.find("FormGroup[label='Description']").length).toBe(1);
    expect(wrapper.find("VariablesField[label='Variables']").length).toBe(1);
  });
});
