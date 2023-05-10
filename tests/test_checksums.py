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

import unittest

from scm.kineis.checksums import get_bch32_calculator, get_fcs32_calculator, get_crc16_calculator


class TestChecksums(unittest.TestCase):
    bch_32 = get_bch32_calculator()
    fcs_32 = get_fcs32_calculator()
    crc_16 = get_crc16_calculator()

    test_data = bytes([x for x in range(16)])

    def test_crc16(self):
        res = self.crc_16.checksum(self.test_data)
        self.assertEqual(20797, res)

    def test_bch32(self):
        res = self.bch_32.checksum(self.test_data)
        self.assertEqual(res, 1212914945)

    def test_fcs32(self):
        res = self.fcs_32.checksum(self.test_data)
        self.assertEqual(res, 4233616773)


if __name__ == "__main__":
    unittest.main()