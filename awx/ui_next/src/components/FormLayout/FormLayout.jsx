import styled from 'styled-components';

export const FormColumnLayout = styled.div`
  width: 100%;
  grid-column: 1 / -1;
  display: grid;
  grid-gap: var(--pf-c-form--GridGap);
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));

  @media (min-width: 1210px) {
    grid-template-columns: repeat(3, 1fr);
  }
`;

export const FormFullWidthLayout = styled.div`
  grid-column: 1 / -1;
  display: grid;
  grid-template-columns: 1fr;
  grid-gap: var(--pf-c-form--GridGap);
`;

export const FormCheckboxLayout = styled.div`
  display: flex;
  justify-content: flex-start;
  flex-wrap: wrap;
  margin-bottom: -10px;
  margin-right: -30px !important;

  & > * {
    margin-bottom: 10px;
    margin-right: 30px;
  }
`;

export const SubFormLayout = styled.div`
  grid-column: 1 / -1;
  background-color: #f5f5f5;
  margin-right: calc(var(--pf-c-card--child--PaddingRight) * -1);
  margin-left: calc(var(--pf-c-card--child--PaddingLeft) * -1);
  padding: var(--pf-c-card--child--PaddingRight);

  & > .pf-c-title {
    --pf-c-title--m-md--FontWeight: 700;
    grid-column: 1 / -1;
    margin-bottom: 20px;
  }
`;
