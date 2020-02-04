import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '@testUtils/enzymeHelpers';
import WorkflowJobTemplateForm from './WorkflowJobTemplateForm';

describe('<WorkflowJobTemplateForm/>', () => {
  let wrapper;
  const handleSubmit = jest.fn();
  const handleCancel = jest.fn();
  const mockTemplate = {
    id: 6,
    name: 'Foo',
    description: 'Foo description',
    summary_fields: {
      inventory: { id: 1, name: 'Inventory 1' },
      organization: { id: 1, name: 'Organization 1' },
      labels: {
        results: [{ name: 'Label 1', id: 1 }, { name: 'Label 2', id: 2 }],
      },
    },
    scm_branch: 'devel',
    limit: '5000',
    variables: '---',
  };
  beforeEach(() => {
    act(() => {
      wrapper = mountWithContexts(
        <WorkflowJobTemplateForm
          template={mockTemplate}
          handleCancel={handleCancel}
          handleSubmit={handleSubmit}
        />
      );
    });
  });
  afterEach(() => {
    wrapper.unmount();
    jest.clearAllMocks();
  });
  test('renders successfully', () => {
    expect(wrapper.length).toBe(1);
  });
  test('all the fields render successfully', () => {
    const fields = [
      'name',
      'description',
      'organization',
      'inventory',
      'limit',
      'scmBranch',
      'labels',
      'variables',
    ];
    const assertField = (field, index) => {
      expect(
        wrapper
          .find('Field')
          .at(index)
          .prop('name')
      ).toBe(`${field}`);
    };
    fields.map((field, index) => assertField(field, index));
  });
  test('changing inputs should update values', async () => {
    const inputsToChange = [
      { element: 'wfjt-name', value: { value: 'new foo', name: 'name' } },
      {
        element: 'wfjt-description',
        value: { value: 'new bar', name: 'description' },
      },
      { element: 'wfjt-limit', value: { value: 1234567890, name: 'limit' } },
      {
        element: 'wfjt-scmBranch',
        value: { value: 'new branch', name: 'scmBranch' },
      },
    ];
    const changeInputs = async ({ element, value }) => {
      wrapper.find(`input#${element}`).simulate('change', {
        target: value,
      });
    };

    await act(async () => {
      inputsToChange.map(input => changeInputs(input));
      wrapper.find('LabelSelect').invoke('onChange')([
        { name: 'new label', id: 5 },
        { name: 'Label 1', id: 1 },
        { name: 'Label 2', id: 2 },
      ]);
      wrapper.find('InventoryLookup').invoke('onChange')({
        id: 3,
        name: 'inventory',
      });
      wrapper.find('OrganizationLookup').invoke('onChange')({
        id: 3,
        name: 'organization',
      });
    });
    wrapper.update();
    const assertChanges = ({ element, value }) => {
      expect(wrapper.find(`input#${element}`).prop('value')).toEqual(
        typeof value.value === 'string' ? `${value.value}` : value.value
      );
    };

    inputsToChange.map(input => assertChanges(input));
    expect(wrapper.find('InventoryLookup').prop('value')).toEqual({
      id: 3,
      name: 'inventory',
    });
    expect(wrapper.find('OrganizationLookup').prop('value')).toEqual({
      id: 3,
      name: 'organization',
    });
    expect(wrapper.find('LabelSelect').prop('value')).toEqual([
      { name: 'new label', id: 5 },
      { name: 'Label 1', id: 1 },
      { name: 'Label 2', id: 2 },
    ]);
  });
  test('handleSubmit is called on submit button click', async () => {
    await act(async () => {
      await wrapper.find('button[aria-label="Save"]').simulate('click');
    });

    act(() => {
      expect(handleSubmit).toBeCalled();
    });
  });
  test('handleCancel is called on cancel button click', () => {
    act(() => {
      wrapper.find('button[aria-label="Cancel"]').simulate('click');
    });

    expect(handleCancel).toBeCalled();
  });
});
