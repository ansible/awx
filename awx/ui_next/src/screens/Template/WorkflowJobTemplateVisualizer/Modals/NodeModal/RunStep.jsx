import React from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import styled from 'styled-components';
import { Title } from '@patternfly/react-core';
import { SelectableCard } from '@components/SelectableCard';

const Grid = styled.div`
  display: grid;
  grid-template-columns: 33% 33% 33%;
  grid-gap: 20px;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  grid-auto-rows: 100px;
  width: 100%;
  margin: 20px 0px;
`;

function RunStep({ i18n, linkType, updateLinkType }) {
  return (
    <>
      <Title headingLevel="h1" size="xl">
        {i18n._(t`Run`)}
      </Title>
      <p>
        {i18n._(
          t`Specify the conditions under which this node should be executed`
        )}
      </p>
      <Grid>
        <SelectableCard
          isSelected={linkType === 'success'}
          label={i18n._(t`On Success`)}
          description={i18n._(
            t`Execute when the parent node results in a successful state.`
          )}
          onClick={() => updateLinkType('success')}
        />
        <SelectableCard
          isSelected={linkType === 'failure'}
          label={i18n._(t`On Failure`)}
          description={i18n._(
            t`Execute when the parent node results in a failure state.`
          )}
          onClick={() => updateLinkType('failure')}
        />
        <SelectableCard
          isSelected={linkType === 'always'}
          label={i18n._(t`Always`)}
          description={i18n._(
            t`Execute regardless of the parent node's final state.`
          )}
          onClick={() => updateLinkType('always')}
        />
      </Grid>
    </>
  );
}

export default withI18n()(RunStep);
