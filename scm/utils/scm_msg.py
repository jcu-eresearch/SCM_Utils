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

import struct
from decimal import Decimal
from functools import lru_cache
from collections import OrderedDict
from geographiclib.geodesic import Geodesic


from scm.generated.SCM_DF import scm_df_decode, SCM_DF_Transmission_Payload, SCM_DF_TEMP_MAX_LOW, \
    SCM_DF_TRACKING_LONGITUDE_SIZE, SCM_DF_TRACKING_LATITUDE_SIZE, SCM_DF_BAT_RANGE_LOW, SCM_DF_BAT_RANGE_HIGH, \
    SCM_DF_TRACKING_BATTERY_SIZE, SCM_DF_TEMP_MIN_HIGH, SCM_DF_TEMP_MIN_LOW, SCM_DF_TRACKING_TEMP_MIN_SIZE, \
    SCM_DF_TEMP_MAX_HIGH, SCM_DF_TRACKING_TEMP_MAX_SIZE, SCM_DF_POINT_DELTA_M_SIZE, SCM_DF_POINT_DELTA_ANGLE_SIZE

from scm.utils.constants import *


def scm_message_decode(raw_message):
    """
    scm_message_decode decodes and converts the raw_message to an OrderedDict by calling scm.generated.scm_df_decode.
    scm_message_decode then converts the decoded quantized values into real world values.

    :param raw_message: The raw message represented as a Hex encoded string.
                        For example: "03dc8000002022fd2fed93000d66600000000000000000000000007eb450de"
    :return: An OrderedDict containing the decoded data.
    """
    unpacked = scm_df_decode(raw_message)
    result = OrderedDict()

    # Copy over the CRC, DF, MC and packet_typpe
    for key in [transmission_crc16, transmission_SF, transmission_MC, transmission_packet_type]:
        result[key] = unpacked[key]

    # If this is a tracking packet, unpack it.
    if unpacked[transmission_packet_type] == SCM_DF_Transmission_Payload.SCM_DF_Transmission_Payload_Tracking:
        result[transmission_payload] = OrderedDict()
        result[transmission_payload][transmission_payload_tracking] = OrderedDict()

        tracking_payload = unpacked[transmission_payload][transmission_payload_tracking]
        result_tracking_payload = result[transmission_payload][transmission_payload_tracking]

        # Convert Flags
        result_tracking_payload[transmission_payload_tracking_flags] = \
            tracking_payload[transmission_payload_tracking_flags]

        # Convert Timeslot
        result_tracking_payload[transmission_payload_tracking_timeslot] = \
            tracking_payload[transmission_payload_tracking_timeslot] * 2

        # Convert Longitude
        result_tracking_payload[transmission_payload_tracking_longitude] = \
            unpack_signed_int_32(
                tracking_payload[transmission_payload_tracking_longitude],
                32 - SCM_DF_TRACKING_LONGITUDE_SIZE
            )[0]
        focus_longitude = result_tracking_payload[transmission_payload_tracking_longitude]

        # Convert Latitude
        result_tracking_payload[transmission_payload_tracking_latitude] = \
            unpack_signed_int_32(
                tracking_payload[transmission_payload_tracking_latitude],
                32 - SCM_DF_TRACKING_LATITUDE_SIZE
            )[0]
        focus_latitude = result_tracking_payload[transmission_payload_tracking_latitude]

        # Convert Orientation
        result_tracking_payload[transmission_payload_tracking_orientation] = \
            tracking_payload[transmission_payload_tracking_orientation]

        # Convert Activity level
        result_tracking_payload[transmission_payload_tracking_activity] = \
            tracking_payload[transmission_payload_tracking_activity]

        # Convert Battery voltage
        result_tracking_payload[transmission_payload_tracking_battery] = \
            (Decimal(tracking_payload[transmission_payload_tracking_battery]) * calculate_battery_step()) + SCM_DF_BAT_RANGE_LOW

        # Convert Temperature Min
        result_tracking_payload[transmission_payload_tracking_temp_min] = \
            (Decimal(tracking_payload[transmission_payload_tracking_temp_min]) * calculate_temp_min_step()) + SCM_DF_TEMP_MIN_LOW

        # Convert Temperature Max
        result_tracking_payload[transmission_payload_tracking_temp_max] = \
            (Decimal(tracking_payload[transmission_payload_tracking_temp_max]) * calculate_temp_max_step()) + SCM_DF_TEMP_MAX_LOW

        # Convert Temperature Alert
        result_tracking_payload[transmission_payload_tracking_temp_alert] = \
            tracking_payload[transmission_payload_tracking_temp_alert] == 1

        # Convert the associated points
        geod = Geodesic.WGS84
        result_tracking_payload[transmission_payload_tracking_points] = []
        result_points = result_tracking_payload[transmission_payload_tracking_points]
        for point in tracking_payload[transmission_payload_tracking_points]:
            print(point)
            res = OrderedDict()
            result_points.append(res)

            # Compute Values
            delta_d_km = point[transmission_payload_tracking_points_delta_km]
            delta_d_m = Decimal(point[transmission_payload_tracking_points_delta_m]) * calculate_point_delta_m_step()
            total_delta_m = (delta_d_km * Decimal(1000)) + delta_d_m
            bearing = Decimal(point[transmission_payload_tracking_points_delta_angle]) * calculate_point_bearing_step()
            activity = point[transmission_payload_tracking_points_activity] 
            temp_alert = point[transmission_payload_tracking_points_temp_alert] == 1
            computed_position = geod.Direct(focus_latitude, focus_longitude, bearing, float(total_delta_m))

            # Populate results
            res[transmission_payload_tracking_points_delta_km] = delta_d_km
            res[transmission_payload_tracking_points_delta_m] = delta_d_m
            res[transmission_payload_tracking_points_total_delta_m] = total_delta_m
            res[transmission_payload_tracking_points_delta_angle] = bearing
            res[transmission_payload_tracking_points_activity] = activity
            res[transmission_payload_tracking_points_temp_alert] = temp_alert
            res[transmission_payload_tracking_latitude]  = computed_position['lat2']
            res[transmission_payload_tracking_longitude] = computed_position['lon2']

    return result


@lru_cache(maxsize=2)
def calculate_battery_step():
    """
    calculate_battery_step calculates the quantized step value for each count of the battery field.
    :return: The step size
    """
    return (SCM_DF_BAT_RANGE_HIGH - SCM_DF_BAT_RANGE_LOW) / (2 ** SCM_DF_TRACKING_BATTERY_SIZE)


@lru_cache(maxsize=2)
def calculate_temp_max_step():
    """
    calculate_temp_max_step calculates the quantized step value for each count of the temp_min field.
    :return:
    """
    return (SCM_DF_TEMP_MAX_HIGH - SCM_DF_TEMP_MAX_LOW) / (2 ** SCM_DF_TRACKING_TEMP_MAX_SIZE)


@lru_cache(maxsize=2)
def calculate_temp_min_step():
    """
    calculate_temp_min_step calculates the quantized step value for each count of the temp_min field.
    :return:
    """
    return (SCM_DF_TEMP_MIN_HIGH - SCM_DF_TEMP_MIN_LOW) / (2 ** SCM_DF_TRACKING_TEMP_MIN_SIZE)


@lru_cache(maxsize=2)
def calculate_point_delta_m_step():
    """
    calculate_point_delta_m_step calculates the quantized step value for each count of the point_delta_m field.
    :return:
    """
    return Decimal('1000') / (2 ** SCM_DF_POINT_DELTA_M_SIZE)


@lru_cache(maxsize=2)
def calculate_point_bearing_step():
    """
    calculate_point_bearing_step calculates the quantized step value for each count of the point_delta_angle field.
    :return:
    """
    return Decimal('360') / (2 ** SCM_DF_POINT_DELTA_ANGLE_SIZE)


def unpack_signed_int_32(value, shift):
    """
    Convert the none 32-bit integer into a 32-bit integer by shifting be the specified amount.
    This is done is such a way to mimic what the result would have been if calculated in C
    :param value: The starting value
    :param shift: The shift amount
    :return: C version of value << shift
    """
    _value_h = hex(value << shift)[2:]
    _value_h = _value_h.zfill(8)
    _value_b = bytes.fromhex(_value_h)
    return struct.unpack(">i", _value_b)
