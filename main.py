# Needs  Neopixel strip on GP15
# Modified from Official Rasp Pi example here:
# https://github.com/micropython/micropython/tree/master/examples/bluetooth
# Tony Goodhew 23 June 2023

import bluetooth
import random
import struct
import time
from ble_advertising import advertising_payload
from micropython import const

# Neopixel additional material ############
from machine import Pin
from neopixel import NeoPixel
strip1 = NeoPixel(Pin(15), 37)
strip2 = NeoPixel(Pin(16), 37)
stripT = NeoPixel(Pin(14), 25)

#   End of LED additional material  #########

_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)

_FLAG_READ = const(0x0002)
_FLAG_WRITE_NO_RESPONSE = const(0x0004)
_FLAG_WRITE = const(0x0008)
_FLAG_NOTIFY = const(0x0010)

_UART_UUID = bluetooth.UUID(0xfff0)
_UART_TX = (
    bluetooth.UUID(0xfff1),
    _FLAG_READ | _FLAG_NOTIFY,
)
_UART_RX = (
    bluetooth.UUID(0xfff2),
    _FLAG_WRITE | _FLAG_WRITE_NO_RESPONSE,
)
_UART_SERVICE = (
    _UART_UUID,
    (_UART_TX, _UART_RX),
)


class BLESimplePeripheral:
    def __init__(self, ble, name="momefilo-ws2812"):
        self._ble = ble
        self._ble.active(True)
        self._ble.irq(self._irq)
        ((self._handle_tx, self._handle_rx),) = self._ble.gatts_register_services((_UART_SERVICE,))
        self._connections = set()
        self._write_callback = None
        self._payload = advertising_payload(name="momefilo-ws2812", services=[_UART_UUID])
        self._advertise()

    def _irq(self, event, data):
        # Track connections so we can send notifications.
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, _, _ = data
            self._connections.add(conn_handle)
        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, _ = data
            self._connections.remove(conn_handle)
            # Start advertising again to allow a new connection.
            self._advertise()
        elif event == _IRQ_GATTS_WRITE:
            conn_handle, value_handle = data
            value = self._ble.gatts_read(value_handle)
            if value_handle == self._handle_rx and self._write_callback:
                self._write_callback(value)

    def send(self, data):
        for conn_handle in self._connections:
            self._ble.gatts_notify(conn_handle, self._handle_tx, data)

    def is_connected(self):
        return len(self._connections) > 0

    def _advertise(self, interval_us=500000):
        self._ble.gap_advertise(interval_us, adv_data=self._payload)

    def on_write(self, callback):
        self._write_callback = callback

def SaveIniFile(filename, valueArray):
    with open(filename, "w") as f:
        for wert in valueArray:
            f.write("{}\n".format(wert))

def LoadIniFile(filename):
    valueArray = []
    with open(filename, "r") as f:
        for s in f:
            valueArray.append((int(s)))
    return bytes(valueArray)

aktuall_led = LedStart = LedEnd = Speed = 0
def demo():    # This part modified to control Neopixel strip
    ble = bluetooth.BLE()
    p = BLESimplePeripheral(ble)
    def writeToStrip(v):
        r1 = v[0]
        g1 = v[1]
        b1 = v[2]
        ledStart = v[3]
        ledEnd = v[4]
        r2 = v[5]
        g2 = v[6]
        b2 = v[7]
        speed = v[8]
        rT = v[9]
        gT = v[10]
        bT = v[11]
        global Speed
        Speed = speed
        global LedStart
        LedStart = ledStart
        global LedEnd
        global aktuall_led
        aktuall_led = 0
        LedEnd = ledEnd
        r_diff = int((r2 - r1)/(ledEnd - ledStart))
        g_diff = int((g2 - g1)/(ledEnd - ledStart))
        b_diff = int((b2 - b1)/(ledEnd - ledStart))
#        print(r_diff, g_diff, b_diff)
        for i in range(ledStart, ledEnd):
            strip1[i] = (r1,g1,b1)
            strip2[i] = (r1,g1,b1)
            r1 += r_diff
            g1 += g_diff
            b1 += b_diff
        # Send the data to the strip
        strip1.write()
        strip2.write()
        for i in range(0, 25):
            stripT[i] = (rT,gT,bT)
        stripT.write()
    
    try:
        valueArray = LoadIniFile("werte.dic")
        writeToStrip(valueArray)
    except:
        print("Fehler load Ini")

    def on_rx(v):  # v is what has been received
        SaveIniFile("werte.dic", v)
        writeToStrip(v)
        
    p.on_write(on_rx)
    
    global aktuall_led
    aktuall_led = 0
    while True:
        if(Speed > 0):
            if aktuall_led < LedEnd:
                tmpcolor0 = strip1[0]
                for i in range(LedStart, LedEnd-1):
                    strip1[i] = strip1[i+1]
                    strip2[i] = strip2[i+1]
                strip1[LedEnd-1] = strip2[LedEnd-1] = tmpcolor0
                aktuall_led += 1
            elif aktuall_led >= LedEnd and aktuall_led <= LedEnd*2:
                tmpcolor0 = strip1[LedEnd-1]
                for i in range(LedEnd - 1, LedStart, -1):
                    strip1[i] = strip1[i-1]
                    strip2[i] = strip2[i-1]
                strip1[LedStart] = strip2[LedStart] = tmpcolor0
                aktuall_led += 1
            if aktuall_led > (LedEnd*2-1):
                aktuall_led = 0
            strip1.write()
            strip2.write()
            time.sleep(1/Speed)

if __name__ == "__main__":
    demo()
