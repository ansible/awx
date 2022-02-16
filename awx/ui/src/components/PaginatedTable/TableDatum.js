import { Td } from '@patternfly/react-table';
import { TdBreakWord } from 'components/PaginatedTable';

export default function TableDatum({
  value,
  dataLabel,
  select = null,
  expand = null,
  breakword,
  id,
}) {
  if (select) {
    return <Td select={select} />;
  }
  if (expand) {
    return <Td expand={expand} />;
  }
  if (breakword) {
    return value ? (
      <TdBreakWord id={id} dataLabel={dataLabel}>
        {value}
      </TdBreakWord>
    ) : (
      <TdBreakWord dataLabel={dataLabel} />
    );
  }
  return value ? (
    <Td dataLabel={dataLabel}>{value}</Td>
  ) : (
    <Td dataLabel={dataLabel} />
  );
}
