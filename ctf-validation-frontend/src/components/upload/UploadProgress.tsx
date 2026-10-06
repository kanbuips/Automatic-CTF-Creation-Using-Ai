export default function UploadProgress({ fraction }: { fraction: number }) {
  return (
    <div className="progress" aria-label="upload progress">
      <div style={{ width: `${Math.round(fraction * 100)}%` }} />
    </div>
  );
}
