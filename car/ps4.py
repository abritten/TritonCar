import time
import asyncio
import evdev
from evdev import InputDevice, categorize, ecodes
from multiprocessing import Process, Manager

import socket
import json

from utils import parse_packet

def update_inputs(dev, data):
    async def update_inputs(dev, data):
        async for event in dev.async_read_loop():
            data["timestamp"] = time.time()
            if event.type == 1:
                if(event.code == 304):
                    data["square"] = event.value
                if(event.code == 306):
                    data["circle"] = event.value
                if(event.code == 307):
                    data["triangle"] = event.value
                if(event.code == 305):
                    data["cross"] = event.value

            # 0 to 255
            elif(event.type == 3):
                if(event.code == 1):
                    data["ly"] = event.value
                elif(event.code == 2):
                    data["rx"] = event.value

    asyncio.ensure_future(update_inputs(dev, data))
    loop = asyncio.get_event_loop()
    loop.run_forever()


def read_controller_socket(data, conn_type="TCP", frequency=20, port=8080):
    if conn_type=="UDP":
        raise ValueError("do not use UDP sockets")
    elif conn_type=="TCP":
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("192.168.22.207", port))
        while True:
            start = time.time()
            pkt = s.recv(128)
            parse_packet(pkt, data)
            data["timestamp"] = time.time()
            while time.time()<(start+1.0/frequency):
                pass


class PS4Interface:
    def __init__(self, connection_type="websocket_TCP"):
        manager = Manager()
        self.data = manager.dict({
            "cross": 0,
            "square": 0,
            "triangle": 0,
            "circle": 0,
            "ly": 128,
            "rx": 128, 
            "timestamp":time.time()
        })

        if connection_type=="bluetooth":
            devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
            path=None
            for device in devices:
                if("Wireless Controller" in device.name):
                    path = device.path
            dev = InputDevice(path)
            controller_process = Process(target=update_inputs, args=(dev, self.data))
        
        elif connection_type=="websocket_TCP":
            controller_process = Process(target=read_controller_socket, args=(self.data,))
            
        controller_process.start()