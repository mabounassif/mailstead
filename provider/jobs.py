from jobs.worker_runtime import register


@register("noop")
def _noop(_job):
    return
