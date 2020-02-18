import styled from 'styled-components';

export const FormColumnLayout = styled.div`
  width: 100%;
  grid-column: 1 / 4;
  display: grid;
  grid-gap: 20px;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));

  @media (min-width: 1210px) {
    grid-template-columns: repeat(3, 1fr);
  }
`;

export const FormFullWidthLayout = styled.div`
  grid-column: 1 / -1;
  display: grid;
  grid-template-columns: 1fr;
  grid-gap: 20px;
`;

export const FormCheckboxLayout = styled.div`
  display: flex;
  justify-content: flex-start;
  flex-wrap: wrap;

  & > * {
    margin-right: 30px;
    margin-bottom: 10px;
  }
`;

export const SubFormLayout = styled.div`
  grid-column: 1 / -1;
  background-color: #f5f5f5;
  margin: 0 -24px;
  padding: 24px;

  & > .pf-c-title {
    --pf-c-title--m-md--FontWeight: 700;
    grid-column: 1 / -1;
    margin-bottom: 20px;
  }
`;
