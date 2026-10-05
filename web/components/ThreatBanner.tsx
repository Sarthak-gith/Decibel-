import type { DecibelState } from "@/lib/types";

export default function ThreatBanner({ state }: { state: DecibelState }) {
  return state === "THREAT_DETECTED" ? <div className="threat-banner" role="alert"><span aria-hidden="true">⚠</span><strong>Possible AI-cloned voice detected. Do not share OTP or money.</strong><span className="eyebrow">Screening alert</span></div> : null;
}
