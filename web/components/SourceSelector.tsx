export type SourceLabel = "phone" | "speakerphone" | "tab";

export default function SourceSelector({ value, onChange, disabled }: { value: SourceLabel; onChange: (source: SourceLabel) => void; disabled: boolean }) {
  return <section className="panel source-panel"><label htmlFor="audio-source" className="eyebrow">Capture source</label><select id="audio-source" value={value} onChange={(event) => onChange(event.target.value as SourceLabel)} disabled={disabled}><option value="phone">Phone mode</option><option value="speakerphone">Speakerphone</option><option value="tab">Tab audio</option></select><p className="panel-footnote">{value === "tab" ? "Share a browser tab and enable tab audio." : "Uses this device’s microphone. Browser capture only."}</p></section>;
}
