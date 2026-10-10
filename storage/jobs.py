from jobs.worker_runtime import register
from storage.services import sweep_expired_reservations


@register("storage_sweep")
def handle_storage_sweep(_job):
    sweep_expired_reservations()
