import React from 'react';

import { useField } from 'formik';
import { t } from '@lingui/macro';
import styled from 'styled-components';
import { Title } from '@patternfly/react-core';
import SelectableCard from 'components/SelectableCard';

const Grid = styled.div`
  display: grid;
  grid-auto-rows: 100px;
  grid-gap: 20px;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  margin: 20px 0px;
  width: 100%;
`;

function RunStep() {
  const [field, , helpers] = useField('linkType');
  return (
    <>
      <Title headingLevel="h1" size="xl">
        {t`Run`}
      </Title>
      <p>
        {t`Specify the conditions under which this node should be executed`}
      </p>
      <Grid>
        <SelectableCard
          id="link-type-success"
          isSelected={field.value === 'success'}
          label={t`On Success`}
          description={t`Execute when the parent node results in a successful state.`}
          onClick={() => helpers.setValue('success')}
        />
        <SelectableCard
          id="link-type-failure"
          isSelected={field.value === 'failure'}
          label={t`On Failure`}
          description={t`Execute when the parent node results in a failure state.`}
          onClick={() => helpers.setValue('failure')}
        />
        <SelectableCard
          id="link-type-always"
          isSelected={field.value === 'always'}
          label={t`Always`}
          description={t`Execute regardless of the parent node's final state.`}
          onClick={() => helpers.setValue('always')}
        />
      </Grid>
    </>
  );
}
export default RunStep;
