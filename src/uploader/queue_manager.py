"""
Queue Manager Module
Handles upload task queueing and progress emission.
"""

class UploadTask:
    """
    Represents a single upload task.
    Args:
        file_path: Path to video file
        metadata: Dict with title, description, tags, etc.
    """
    def __init__(self, file_path, metadata):
        self.file_path = file_path
        self.metadata = metadata
        # TODO: Add more fields if needed


class UploadQueue:
    """
    Manages a queue of UploadTask objects and uploads them sequentially.
    Emits progress via callback.
    """
    def __init__(self):
        self.tasks = []
        self.is_running = False

    def add_task(self, task):
        """Add an UploadTask to the queue."""
        self.tasks.append(task)

    def start(self, progress_callback=None):
        """
        Start uploading tasks sequentially.
        Emits progress via callback.
        """
        self.is_running = True
        # TODO: Sequentially upload tasks, emit progress
        pass
