import time
from itertools import chain
from typing import Optional, Union

from osc4py3 import oscbuildparse
from osc4py3.as_eventloop import *
from osc4py3.oscmethod import *

from ..utils import alias_param
from .osc_loop import OSCLoop
from .sender import Number, NumericElement, Sender, StringElement
import asyncio

__all__ = ("MRPHandler",)


class MRPHandler(Sender):
    def __init__(
        self,
        loop: OSCLoop,
        ip: str = "127.0.0.1",
        port: int = 7770,
        name: str = "MRPHandler",
        ahead_amount: float = 0.0,
    ):
        super().__init__()
        self.loop = loop
        loop.add_child(self)
        self.active_notes: dict[tuple[int, int], asyncio.Task] = {}

        # Setting up OSC Connexion
        self._ip, self._port, self._name = (ip, port, name)
        self._ahead_amount = ahead_amount
        self.client = osc_udp_client(address=self._ip, port=self._port, name=self._name)
        self._events = {"send": self._send}

    def __repr__(self) -> str:
        return f"<{type(self).__name__} {self._name} ip={self._ip!r} port={self._port}>"

    def setup(self):
        for event in self._events:
            self.env.register_hook(event, self)

    def hook(self, event: str, *args):
        func = self._events[event]
        func(*args)

    def _note_on(self, note: int) -> None:
        self._send('/mrp/midi', [0x9F, note, 127])

    def _note_off(self, note: int) -> None:
        self._send('/mrp/midi', [0x8F, note, 0])

    def _send(self, address: str, message: list) -> None:
        msg = oscbuildparse.OSCMessage(address, None, message)
        bun = oscbuildparse.OSCBundle(
            oscbuildparse.unixtime2timetag(time.time() + self._ahead_amount),
            [msg],
        )
        osc_send(bun, self._name)

    def send_midi_note(self, note: int, duration: float, address: str = '/mrp/midi') -> None:
        """
        TODO: Rewrite that docstring
        """

        key = (note, 15)
        note_task = self.active_notes.get(key)

        if note_task is not None and not note_task.done():
            self._note_off(note=note)
            note_task.cancel()
            self.active_notes.pop(key, None)

        self._note_on(note=note) 
        self.active_notes[key] = asyncio.create_task(
            self.send_off(address=address, note=note, delay=duration - 0.02,
            )
        )

    async def send_off(self, address: str, note: int, delay: Union[int, float]):
        await self.env.sleep(delay)
        self._note_off(note=note)
        self.active_notes.pop((note, 15), None)

    @alias_param(name="duration", alias="dur")
    @alias_param(name="iterator", alias="i")
    @alias_param(name="divisor", alias="d")
    @alias_param(name="rate", alias="r")
    def send_note(
        self,
        note: Optional[NumericElement] = 60,
        duration: NumericElement = 1,
        iterator: Number = 0,
        divisor: NumericElement = 1,
        rate: NumericElement = 1,
    ) -> None:
        if note is None:
            return

        # MRP()
        pattern = {
            "note": note,
            "duration": duration,
        }
        for message in self.pattern_reduce(pattern, iterator, divisor, rate):
            if message["note"] is None:
                continue
            for k in ("note", "duration"):
                message[k] = int(message[k])
            self.send_midi_note(**message)

    @alias_param(name="quality", alias="q")
    @alias_param(name="value", alias="v")
    @alias_param(name="iterator", alias="i")
    @alias_param(name="divisor", alias="d")
    @alias_param(name="rate", alias="r")
    def send_quality(
        self,
        iterator: Number = 0,
        divisor: NumericElement = 1,
        rate: NumericElement = 1,
        **pattern: NumericElement,
    ) -> None:

        pattern["address"] = 'blah'
        for message in self.pattern_reduce(pattern, iterator, divisor, rate):
            # TODO: Remove 'blah' from message list
            address = '/mrp/quality/'+message.pop("quality")
            serialized = list(chain(message.values()))[:-1]
            self._send(f"/{address}", serialized)
