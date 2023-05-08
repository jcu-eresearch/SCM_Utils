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

from crc import Calculator, Configuration

CRC16_POLYNOMIAL = 0x1021
BCH32_POLYNOMIAL = 0xEE5B42FD
FCS32_POLYNOMIAL = 0x04C11DB7


def get_bch32_calculator():
    """
    get_bch32_calculator creates a 32-bit CRC calculator for computing the BCH32 error correction code placed
    at the end of an ARGOS transmission data packet.
    :return: The CRC calculator that can compute the BCH32
    """
    config = Configuration(
        width=32,
        polynomial=BCH32_POLYNOMIAL,
        init_value=0x00,
        final_xor_value=0x00,
        reverse_input=False,
        reverse_output=False,
    )
    return Calculator(config)


def get_fcs32_calculator():
    config = Configuration(
        width=32,
        polynomial=FCS32_POLYNOMIAL,
        init_value=0x00,
        final_xor_value=0x00,
        reverse_input=False,
        reverse_output=False,
    )
    return Calculator(config)


def get_crc16_calculator():
    """
    get_crc16_calculator creates a 16-bit CRC calculator for computing the CRC16 checksum placed at the beginning
    of the ARGOS transmission data packet.
    :return: The CRC calculator that can compute the CRC16
    """
    config = Configuration(
        width=16,
        polynomial=CRC16_POLYNOMIAL,
        init_value=0x00,
        final_xor_value=0x00,
        reverse_input=False,
        reverse_output=False,
    )
    return Calculator(config)
