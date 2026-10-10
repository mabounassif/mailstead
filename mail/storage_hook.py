"""M2 stub; M3 replaces with real reserve-then-write."""

from contextlib import contextmanager


@contextmanager
def reserve_inbound_bytes(mailbox, nbytes: int):
    yield
