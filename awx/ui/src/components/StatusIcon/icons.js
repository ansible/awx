import styled, { keyframes } from 'styled-components';
import {
  CheckCircleIcon,
  ExclamationCircleIcon,
  SyncAltIcon,
  ExclamationTriangleIcon,
  ClockIcon,
  MinusCircleIcon,
  InfoCircleIcon,
} from '@patternfly/react-icons';

const Spin = keyframes`
  from {
    transform: rotate(0);
  }
  to {
    transform: rotate(1turn);
  }
`;

const RunningIcon = styled(SyncAltIcon)`
  animation: ${Spin} 1.75s linear infinite;
`;
RunningIcon.displayName = 'RunningIcon';

const icons = {
  approved: CheckCircleIcon,
  denied: InfoCircleIcon,
  success: CheckCircleIcon,
  healthy: CheckCircleIcon,
  successful: CheckCircleIcon,
  ok: CheckCircleIcon,
  failed: ExclamationCircleIcon,
  error: ExclamationCircleIcon,
  unreachable: ExclamationCircleIcon,
  running: RunningIcon,
  pending: ClockIcon,
  waiting: ClockIcon,
  disabled: MinusCircleIcon,
  skipped: MinusCircleIcon,
  canceled: ExclamationTriangleIcon,
  changed: ExclamationTriangleIcon,
};
export default icons;
