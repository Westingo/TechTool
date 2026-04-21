import asyncio

class EventBus:
    def __init__(self):
        self._subscribers = []

    def subscribe(self):
        queue = asyncio.Queue()
        self._subscribers.append(queue)
        return queue

    def unsubscribe(self, queue):
        self._subscribers.remove(queue)

    def publish(self, event):
        for queue in self._subscribers:
            queue.put_nowait(event)

bus = EventBus()
