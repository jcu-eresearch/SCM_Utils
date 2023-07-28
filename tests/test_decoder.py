# SCM_Utils is a library of utilities for the Space Cows Project
#
# MIT License
#
# Copyright (c) 2023 eResearch Centre, James Cook University
# Author: Nigel Bajema
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import json
from copy import deepcopy
from json import loads, dumps
from unittest import TestCase

from scm.generated.SCM_DF import BitQueue
from scm.utils.constants import transmission_bch32_verified, transmission_crc16_verified, transmission_crc16, \
    transmission_bch32, transmission_decoded_type, transmission_decoded_raw_type
from scm.utils.helpers import TransmissionEncoder
from scm.utils.scm_epoch import DeviceEpoch
from scm.utils.scm_msg import scm_raw_message_decode, scm_processed_message_decode


class TestDecoder(TestCase):
    raw = {
            "ts": 1682984022243,
            "values": {
                   "device_id": 184999,
                   "msg_date": "2023-05-01T23:33:42.243Z",
                   "msg_id": "1102749036487643137",
                   "raw_data": "013a4049000045fb1fdb210000000007840000041e2000032f2400002e2930"
                }
           }

    processed = {
        "ts": 1682984022243,
        "values": {
            "msg_date": "2023-05-01T23:33:42.243Z",
            "device_id": 184999,
            "msg_id": "1102764137706070016",
            "RAW_DATA": "000045FB1FDB210000000007840000041E2000032F2400",
            "SERVICE_FLAG": 0,
            "MESSAGE_COUNTER": 73,
            "CRC_OK": True,
            "checked": "Y"
        }
    }
    
    result = {
        "id": 0, 
        "crc16": 5028, 
        "SF": 0, 
        "MC": 73, 
        "packet_type": 0, 
        "payload": {
            "tracking_v1_0": {
                "flags": 0, 
                "timeslot": 0, 
                "longitude": "146.75968", 
                "latitude": "-19.331072", 
                "orientation": 0, 
                "activity": 0, 
                "battery": "3.00", 
                "temp_min": "0.0", 
                "temp_max": "20.0", 
                "temp_alert": False, 
                "points": [
                    {
                        "delta_km": 0, 
                        "delta_m": "234.3750", 
                        "total_delta_m": "234.3750", 
                        "delta_angle": "22.50000000", 
                        "activity": 0, 
                        "temp_alert": False, 
                        "latitude": -19.32912466132596, 
                        "longitude": 146.76053479568455}, 
                    {
                        "delta_km": 0, 
                        "delta_m": "250.0000", 
                        "total_delta_m": "250.0000", 
                        "delta_angle": "338.90625000", 
                        "activity": 0, 
                        "temp_alert": False, 
                        "latitude": -19.3289743495036, 
                        "longitude": 146.75882251438833}, 
                    {
                        "delta_km": 0, 
                        "delta_m": "390.6250", 
                        "total_delta_m": "390.6250", 
                        "delta_angle": "340.66406250", 
                        "activity": 0, 
                        "temp_alert": False, 
                        "latitude": -19.32775718029063, 
                        "longitude": 146.75844736292584}
                ]
            }
        }, 
        "bch32": 3025200, 
        "crc16_verified": True,
        "bch32_verified": True,
        "decode_type": "raw"
    }

    def test_decoder_raw(self):
        message = scm_raw_message_decode(self.raw['values']['raw_data'], DeviceEpoch().get_device_epoch(self.raw['values']['device_id']))
        self.assertTrue(message[transmission_crc16_verified])
        self.assertTrue(message[transmission_bch32_verified])
        self.assertEqual(self.result, loads(dumps(message, cls=TransmissionEncoder)))

    def test_decoder_processed(self):
        message = scm_processed_message_decode(
            self.processed['values']['RAW_DATA'],
            extra_id=0,
            service_flag=self.processed['values']['SERVICE_FLAG'],
            message_counter=self.processed['values']['MESSAGE_COUNTER'],
            crc16_ok=self.processed['values']['CRC_OK'],
            bch32_ok=self.processed['values']['checked'].upper() == "Y"
        )
        answer = deepcopy(message)
        answer[transmission_crc16] = self.result[transmission_crc16]
        answer[transmission_bch32] = self.result[transmission_bch32]
        answer[transmission_decoded_type] = transmission_decoded_raw_type

        self.assertEqual(self.result, loads(dumps(answer, cls=TransmissionEncoder)))
        
    def test_status_decode(self):
        msg = "02642000132337907800003F384096000000000000000000000000B35E63CC".replace(" ", "")
        message = scm_raw_message_decode(msg, DeviceEpoch().get_device_epoch(None))
        from pprint import pprint
        pprint(message)
        print(json.dumps(message, cls=TransmissionEncoder))

    def test_status_decode_2(self):
        msg = "13260D9C0000003F3A0096000000000000000000000000".replace(" ", "")
        message = scm_processed_message_decode(msg, DeviceEpoch().get_device_epoch(None))
        from pprint import pprint
        pprint(message)
        print(json.dumps(message, cls=TransmissionEncoder))

    def test_tracking_v2_raw_decoder(self):
        msg = "0F4EE015085C0045FB87F6CDC001490842C0080B0010A002037000C4C7776C"
        message = scm_raw_message_decode(msg.replace(" ", ""), DeviceEpoch().get_device_epoch(None))
        from pprint import pprint
        pprint(message)
        print(json.dumps(message, cls=TransmissionEncoder))

