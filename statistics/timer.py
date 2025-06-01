"""Class to make and manage timers."""

from time import time
from logger import setup_logger

logger = setup_logger(__name__)


class Timer:
    """Class to make and manage timers"""

    def __init__(self) -> None:
        """Sets up a list of all timers."""
        self.timers = []

    def start(self, timer_id=None) -> str:
        """Starts a timer, and makes an id if no."""
        start = time()
        if not timer_id:
            timer_id = str(len(self.timers) + 1)

        self.timers.append({"id": timer_id, "start": start})
        return timer_id

    def stop(self, timer_id: str, log=False) -> float:
        """Stops a timer with its id."""
        end = time()

        timer = self.get(timer_id)
        start = timer["start"]

        duration = round(end - start, 2)

        if log:
            logger.info(f"{timer_id} took {duration} seconds.")
        return duration

    def get(self, timer_id: str) -> dict:
        """Gets the start, stop and duration time of a timer."""
        for timer in self.timers:
            if timer["id"] == timer_id:
                return timer
        return {}


if __name__ == "__main__":
    example_timer = Timer()
    timer_name = example_timer.start()
    example_timer.stop(timer_name)
    print(example_timer.get(timer_name))
