"""RQ worker entrypoint. Consumes background research jobs from Redis."""

import logging

from redis import Redis
from rq import Queue, Worker

from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("worker")


def main() -> None:
    conn = Redis.from_url(settings.redis_url)
    queue = Queue("research", connection=conn)
    logger.info("Worker started, listening on 'research' queue at %s", settings.redis_url)
    worker = Worker([queue], connection=conn)
    worker.work(with_scheduler=True)


if __name__ == "__main__":
    main()
