import { useRef, useState } from "react";
import { formatBytes } from "../../utils/format";

interface Props {
  label: string;
  accept: string;
  file: File | null;
  onFile: (f: File | null) => void;
}

export default function FileDropzone({ label, accept, file, onFile }: Props) {
  const input = useRef<HTMLInputElement>(null);
  const [over, setOver] = useState(false);
  return (
    <div
      className={`dropzone ${over ? "over" : ""}`}
      onClick={() => input.current?.click()}
      onDragOver={(e) => { e.preventDefault(); setOver(true); }}
      onDragLeave={() => setOver(false)}
      onDrop={(e) => { e.preventDefault(); setOver(false); onFile(e.dataTransfer.files[0] ?? null); }}
    >
      <input ref={input} type="file" accept={accept} hidden onChange={(e) => onFile(e.target.files?.[0] ?? null)} />
      <strong>{label}</strong>
      <span className="muted">{file ? `${file.name} (${formatBytes(file.size)})` : `Drop a file or click (${accept})`}</span>
    </div>
  );
}
