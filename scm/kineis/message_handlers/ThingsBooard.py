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
from scm.kineis.message_handlers.base import KineisMessageHandler, CorruptedMessage
from scm.utils.scm_epoch import DeviceEpoch
from scm.utils.scm_msg import scm_is_bch32_ok, scm_processed_message_decode

values_key = "values"
raw_data_key = "RAW_DATA"
crc_key = "CRC_OK"
checked_key = "checked"
bch_status_key = "BCH_STATUS"
device_id_key = "device_id"


class ThingsBoardProcessedExpert(KineisMessageHandler):

    def validate_message(self, message):
        checked = None
        bch32_status = None
        if values_key in message:
            values = message[values_key]
            if checked_key in values:
                checked = values[checked_key]

            if bch_status_key in values:
                bch32_status = values[bch_status_key]
        return scm_is_bch32_ok(checked=checked, bch_status=bch32_status) and message[values_key][crc_key]

    def decode_message(self, message):
        if not self.validate_message(message):
            raise CorruptedMessage("The message is corrupt")
        message = scm_processed_message_decode(message[values_key][raw_data_key], DeviceEpoch().get_device_epoch(message[values_key][device_id_key]))
        return message

