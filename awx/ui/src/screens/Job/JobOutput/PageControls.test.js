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
    wrapper = mountWithContexts(<PageControls isFlatMode />);
    findChildren();
    expect(AngleDoubleUpIcon.length).toBe(1);
    expect(AngleDoubleDownIcon.length).toBe(1);
    expect(AngleUpIcon.length).toBe(1);
    expect(AngleDownIcon.length).toBe(1);
  });

  test('should render expand/collapse all', () => {
    wrapper = mountWithContexts(
      <PageControls isFlatMode={false} isTemplateJob />
    );
    const expandCollapse = wrapper.find('PageControls__ExpandCollapseWrapper');
    expect(expandCollapse).toHaveLength(1);
    expect(expandCollapse.find('AngleDownIcon')).toHaveLength(1);
    expect(expandCollapse.find('AngleRightIcon')).toHaveLength(0);
  });

  test('should render correct expand/collapse angle icon', () => {
    wrapper = mountWithContexts(
      <PageControls isFlatMode={false} isAllCollapsed isTemplateJob />
    );

    const expandCollapse = wrapper.find('PageControls__ExpandCollapseWrapper');
    expect(expandCollapse).toHaveLength(1);
    expect(expandCollapse.find('AngleDownIcon')).toHaveLength(0);
    expect(expandCollapse.find('AngleRightIcon')).toHaveLength(1);
  });

  test('Should not render expand/collapse all', () => {
    wrapper = mountWithContexts(
      <PageControls isFlatMode={false} isAllCollapsed isTemplateJob={false} />
    );

    const expandCollapse = wrapper.find('PageControls__ExpandCollapseWrapper');
    expect(expandCollapse.find('AngleDownIcon')).toHaveLength(0);
    expect(expandCollapse.find('AngleRightIcon')).toHaveLength(0);
  });
});
