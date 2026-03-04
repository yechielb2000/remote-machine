import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Iterable, List

from ..logging import get_logger
from .result import ParallelResult

logger = get_logger(__name__)


class ParallelExecutor:
    def __init__(self, max_workers: int = 10):
        if max_workers <= 0:
            raise ValueError("max_workers must be > 0")
        self.max_workers = max_workers

    def run(self, clients: Iterable, command: str) -> List[ParallelResult]:
        """
        Run the same command across multiple RemoteMachine instances in parallel.
        """

        results: List[ParallelResult] = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_map = {
                executor.submit(self._execute, client, command): client
                for client in clients
            }

            for future in as_completed(future_map):
                result = future.result()
                results.append(result)

        return results

    def _execute(self, client, command: str) -> ParallelResult:
        start = time.time()
        try:
            output = client.run(command)
            duration_ms = (time.time() - start) * 1000

            logger.info(
                "parallel_command_success",
                extra={
                    "host": client.host,
                    "duration_ms": duration_ms,
                },
            )

            return ParallelResult(
                host=client.host,
                success=True,
                output=output,
                error=None,
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = (time.time() - start) * 1000

            logger.error(
                "parallel_command_failed",
                extra={
                    "host": client.host,
                    "error": str(e),
                },
            )

            return ParallelResult(
                host=client.host,
                success=False,
                output=None,
                error=e,
                duration_ms=duration_ms,
            )