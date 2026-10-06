import type { ReactNode } from "react";

export interface Column<T> {
  header: string;
  render: (row: T) => ReactNode;
}

export default function Table<T>({ columns, rows, rowKey, empty = "Nothing to show" }: {
  columns: Column<T>[];
  rows: T[];
  rowKey: (row: T) => string | number;
  empty?: string;
}) {
  if (rows.length === 0) return <p className="muted">{empty}</p>;
  return (
    <table className="table">
      <thead>
        <tr>{columns.map((c) => <th key={c.header}>{c.header}</th>)}</tr>
      </thead>
      <tbody>
        {rows.map((r) => (
          <tr key={rowKey(r)}>{columns.map((c) => <td key={c.header}>{c.render(r)}</td>)}</tr>
        ))}
      </tbody>
    </table>
  );
}
