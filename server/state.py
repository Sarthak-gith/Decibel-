import os


class StateMachine:
    """EMA smoothing + hysteresis. All thresholds are tunable (see tools/eval_pack.py)."""
    def __init__(self, alpha=None, threat=None, caution=None, secure=None, need=None, warmup=None):
        alpha = float(os.getenv("STATE_ALPHA", "0.4")) if alpha is None else alpha
        threat = float(os.getenv("STATE_THREAT", "0.70")) if threat is None else threat
        caution = float(os.getenv("STATE_CAUTION", "0.55")) if caution is None else caution
        secure = float(os.getenv("STATE_SECURE", "0.40")) if secure is None else secure
        need = int(os.getenv("STATE_NEED", "3")) if need is None else need
        warmup = int(os.getenv("STATE_WARMUP", "2")) if warmup is None else warmup
        self.alpha, self.threat, self.caution, self.secure = alpha, threat, caution, secure
        self.need, self.warmup = need, warmup
        self.smoothed, self.n_voiced, self.hits, self.state = 0.0, 0, 0, "LISTENING"
        print(f"StateMachine config: alpha={self.alpha} threat={self.threat} caution={self.caution} "
              f"secure={self.secure} need={self.need} warmup={self.warmup}")

    def update(self, p_fake, voiced):
        if not voiced:                      # silence: don't touch the score
            return self.smoothed, self.state
        self.n_voiced += 1
        self.smoothed = p_fake if self.n_voiced == 1 else (1 - self.alpha) * self.smoothed + self.alpha * p_fake
        if self.n_voiced < self.warmup:
            self.state = "ANALYZING"
            return self.smoothed, self.state
        self.hits = self.hits + 1 if self.smoothed >= self.threat else 0
        if self.hits >= self.need:
            self.state = "THREAT_DETECTED"
        elif self.state == "THREAT_DETECTED" and self.smoothed >= self.caution:
            pass                            # hysteresis: stay in threat until clearly lower
        elif self.smoothed >= self.caution:
            self.state = "CAUTION"
        elif self.smoothed < self.secure:
            self.state = "SECURE"
        else:
            self.state = "CAUTION" if self.state == "CAUTION" else "SECURE"
        return self.smoothed, self.state
