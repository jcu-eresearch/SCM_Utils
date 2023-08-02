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
from unittest import TestCase

from scm.kineis.message_handlers.ThingsBooard import ThingsBoardProcessedExpert


class TestDecoder(TestCase):
    test_message = {
            "ts": 1690921219761,
            "values":
            {
                "msg_date": "2023-08-01T20:20:19.761Z",
                "device_id": 185909,
                "msg_id": "1136045366370803712",
                "RAW_DATA": "086A4045B177F685E001800841C039A78010506CAC5000",
                "SERVICE_FLAG": 0,
                "MESSAGE_COUNTER": 12,
                 "CRC_OK": True,
                 "checked": "Y"
             }
    }

    def test_processed_message_handler(self):
        handler = ThingsBoardProcessedExpert()
        self.assertTrue(handler.validate_message(self.test_message))
        print(handler.decode_message(self.test_message))
