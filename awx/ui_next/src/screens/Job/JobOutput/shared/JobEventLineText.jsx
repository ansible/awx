import styled from 'styled-components';

const JobEventLineText = styled.div`
  padding: 0 15px;
  white-space: pre-wrap;
  word-break: break-all;
  word-wrap: break-word;

  .time {
    font-size: 14px;
    font-weight: 600;
    user-select: none;
    background-color: #ebebeb;
    border-radius: 12px;
    padding: 2px 10px;
    margin-left: 15px;
  }

  .content {
    background: var(--pf-global--disabled-color--200);
    background: linear-gradient(
      to right,
      #f5f5f5 10%,
      #e8e8e8 18%,
      #f5f5f5 33%
    );
    border-radius: 5px;
  }
`;

JobEventLineText.displayName = 'JobEventLineText';

export default JobEventLineText;
