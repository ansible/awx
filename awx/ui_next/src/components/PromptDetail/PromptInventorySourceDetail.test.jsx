import React from 'react';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import PromptInventorySourceDetail from './PromptInventorySourceDetail';
import mockInvSource from './data.inventory_source.json';

function assertDetail(wrapper, label, value) {
  expect(wrapper.find(`Detail[label="${label}"] dt`).text()).toBe(label);
  expect(wrapper.find(`Detail[label="${label}"] dd`).text()).toBe(value);
}

describe('PromptInventorySourceDetail', () => {
  let wrapper;

  beforeAll(() => {
    wrapper = mountWithContexts(
      <PromptInventorySourceDetail resource={mockInvSource} />
    );
  });

  afterAll(() => {
    wrapper.unmount();
  });

  test('should render successfully', () => {
    expect(wrapper.find('PromptInventorySourceDetail')).toHaveLength(1);
  });

  test('should render expected details', () => {
    assertDetail(wrapper, 'Inventory', 'Demo Inventory');
    assertDetail(wrapper, 'Source', 'scm');
    assertDetail(wrapper, 'Project', 'Mock Project');
    assertDetail(wrapper, 'Inventory File', 'foo');
    assertDetail(wrapper, 'Verbosity', '2 (More Verbose)');
    assertDetail(wrapper, 'Cache Timeout', '2 Seconds');
    expect(
      wrapper
        .find('Detail[label="Regions"]')
        .containsAllMatchingElements([
          <span>us-east-1</span>,
          <span>us-east-2</span>,
        ])
    ).toEqual(true);
    expect(
      wrapper
        .find('Detail[label="Instance Filters"]')
        .containsAllMatchingElements([
          <span>filter1</span>,
          <span>filter2</span>,
          <span>filter3</span>,
        ])
    ).toEqual(true);
    expect(
      wrapper
        .find('Detail[label="Only Group By"]')
        .containsAllMatchingElements([
          <span>group1</span>,
          <span>group2</span>,
          <span>group3</span>,
        ])
    ).toEqual(true);
    expect(wrapper.find('CredentialChip').text()).toBe('Cloud: mock cred');
    expect(wrapper.find('VariablesDetail').prop('value')).toEqual(
      '---\nfoo: bar'
    );
    expect(
      wrapper
        .find('Detail[label="Options"]')
        .containsAllMatchingElements([
          <li>Overwrite</li>,
          <li>Overwrite Variables</li>,
          <li>Update on Launch</li>,
          <li>Update on Project Update</li>,
        ])
    ).toEqual(true);
  });

  test('should render "Deleted" details', () => {
    delete mockInvSource.summary_fields.organization;
    wrapper = mountWithContexts(
      <PromptInventorySourceDetail resource={mockInvSource} />
    );
    assertDetail(wrapper, 'Organization', 'Deleted');
  });
});
