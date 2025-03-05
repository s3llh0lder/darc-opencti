import threading

from typing import Dict


class LockManager:
    """Manages thread locks for record processing"""

    def __init__(self):
        self.record_locks: Dict[int, threading.Lock] = {}
        self.global_lock = threading.Lock()

    def acquire_record_lock(self, record_id: int) -> threading.Lock:
        """Get or create a record-specific lock"""
        with self.global_lock:
            if record_id not in self.record_locks:
                self.record_locks[record_id] = threading.Lock()
            return self.record_locks[record_id]
