import numpy as np

class RollingBuffer:
    """Keeps the most recent n samples (float32)."""
    def __init__(self, n, sr=16000):
        self.n, self.sr = n, sr
        self.data = np.zeros(n, dtype=np.float32)
        self.count = 0
    def append(self, x):
        x = np.asarray(x, dtype=np.float32)[-self.n:]
        k = len(x)
        if k == 0:
            return
        self.data = np.concatenate([self.data[k:], x])
        self.count = min(self.count + k, self.n)
    @property
    def seconds(self):
        return self.count / self.sr
    def snapshot(self):
        return self.data[-self.count:].copy() if self.count else self.data[:0].copy()
