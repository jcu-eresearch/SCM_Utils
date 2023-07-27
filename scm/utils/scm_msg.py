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
import math
import struct
from copy import deepcopy
import datetime
from decimal import Decimal
from functools import lru_cache
from collections import OrderedDict

import tzlocal
# from geographiclib.geodesic import Geodesic
from geopy import Point
from geopy.distance import great_circle

from scm.generated.SCM_DF import *
from scm.kineis.checksums import get_crc16_calculator, get_bch32_calculator

from scm.utils.constants import *
from scm.utils.scm_epoch import DeviceEpoch


class SCM_DF_Transmission_Status_v1_0_Mode(Enum):
    UNKNOOWN = 0
    Testing = 1
    Certification = 2
    GPS_Test = 3
    Transmission_Test = 4
    Hibernation = 5
    BLE_Menu = 6
    Deployed = 7
    Pedometer = 8


class BCH32InvalidInputException(Exception): pass


def scm_is_bch32_ok(checked=None, bch_status=None):
    """
    scm_is_bch32_ok determines if the BCH32 checksum has matched properly
    :param checked:
    :param bch_status:
    :return:
    """
    if checked is not None:
        if checked.upper() != "Y":
            return False
    # The BCH_status is simply the number of bits corrected by the BCH, and the value -2 means that there were too many
    # errors to be corrected (up to 4 bit errors corrected for the BCH32).
    if bch_status is not None:
        if bch_status == -2:
            return False
    if checked is None and bch_status is None:
        raise BCH32InvalidInputException("Both check and bch_status are None")
    return True


def scm_raw_message_decode(raw_message, epoch_year):
    """
    scm_message_decode decodes and converts the raw_message to an OrderedDict by calling scm.generated.scm_df_decode.
    scm_message_decode then converts the decoded quantized values into real world values.

    :param raw_message: The raw message represented as a Hex encoded string.
                        For example: "0EBAA003003845FA9FDB24001ACCC0123CF80006BD700002CDEA00F3BFF5B9"
    :return: An OrderedDict containing the decoded and de-quantized data.
    """

    ensure_message_length(raw_message)
    unpacked = scm_df_decode(raw_message)
    scm_validate_checksums(unpacked)
    result = OrderedDict()

    # Copy over the ID, CRC, DF, MC and packet_typpe
    for key in [transmission_id, transmission_crc16, transmission_SF, transmission_MC, transmission_packet_type]:
        result[key] = unpacked[key]

    # If this is a tracking packet, unpack it.
    if unpacked[transmission_packet_type] == SCM_DF_Transmission_Payload.SCM_DF_Transmission_Payload_Tracking_v1_0:
        result[transmission_payload] = OrderedDict()
        result[transmission_payload][transmission_payload_tracking_v1_0] = OrderedDict()

        tracking_payload = unpacked[transmission_payload][transmission_payload_tracking_v1_0]
        result_tracking_payload = result[transmission_payload][transmission_payload_tracking_v1_0]

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
                32 - SCM_DF_TRACKING_V1_0_LONGITUDE_SIZE
            )[0]
        focus_longitude = Decimal(result_tracking_payload[transmission_payload_tracking_longitude]) / Decimal(
            SCM_DF_GPS_MULTIPLIER)
        result_tracking_payload[transmission_payload_tracking_longitude] = focus_longitude

        # Convert Latitude
        result_tracking_payload[transmission_payload_tracking_latitude] = \
            unpack_signed_int_32(
                tracking_payload[transmission_payload_tracking_latitude],
                32 - SCM_DF_TRACKING_V1_0_LATITUDE_SIZE
            )[0]
        focus_latitude = Decimal(result_tracking_payload[transmission_payload_tracking_latitude]) / Decimal(
            SCM_DF_GPS_MULTIPLIER)
        result_tracking_payload[transmission_payload_tracking_latitude] = focus_latitude

        # Convert Orientation
        result_tracking_payload[transmission_payload_tracking_orientation] = \
            tracking_payload[transmission_payload_tracking_orientation]

        # Convert Activity level
        result_tracking_payload[transmission_payload_tracking_activity] = \
            tracking_payload[transmission_payload_tracking_activity]

        # Convert Battery voltage
        result_tracking_payload[transmission_payload_tracking_battery] = \
            (Decimal(tracking_payload[
                         transmission_payload_tracking_battery]) * calculate_v1_0_battery_step()) + SCM_DF_BAT_RANGE_LOW

        # Convert Temperature Min
        result_tracking_payload[transmission_payload_tracking_temp_min] = \
            (Decimal(tracking_payload[
                         transmission_payload_tracking_temp_min]) * calculate_v1_0_temp_min_step()) + SCM_DF_TEMP_MIN_LOW

        # Convert Temperature Max
        result_tracking_payload[transmission_payload_tracking_temp_max] = \
            (Decimal(tracking_payload[
                         transmission_payload_tracking_temp_max]) * calculate_v1_0_temp_max_step()) + SCM_DF_TEMP_MAX_LOW

        # Convert Temperature Alert
        result_tracking_payload[transmission_payload_tracking_temp_alert] = \
            tracking_payload[transmission_payload_tracking_temp_alert] == 1

        # Convert the associated points
        # geod = Geodesic.WGS84
        result_tracking_payload[transmission_payload_tracking_points] = []
        result_points = result_tracking_payload[transmission_payload_tracking_points]
        for point in tracking_payload[transmission_payload_tracking_points]:
            res = OrderedDict()
            result_points.append(res)

            # Compute Values
            delta_d_km = point[transmission_payload_tracking_points_delta_km]
            delta_d_m = Decimal(point[transmission_payload_tracking_points_delta_m]) * calculate_v1_0_point_delta_m_step()
            total_delta_m = (delta_d_km * Decimal(1000)) + delta_d_m
            bearing = Decimal(point[transmission_payload_tracking_points_delta_angle]) * calculate_v1_0_point_bearing_step()
            activity = point[transmission_payload_tracking_points_activity]
            temp_alert = point[transmission_payload_tracking_points_temp_alert] == 1

            # Geodesy Direct Problem:
            #  https://en.wikipedia.org/wiki/Geodesics_on_an_ellipsoid#Geodesics_on_an_ellipsoid_of_revolution
            #
            # From https://en.wikipedia.org/wiki/Geodesics_on_an_ellipsoid#Applications:
            #   The direct and inverse geodesic problems no longer play the central role in geodesy that they once did.
            #   Instead of solving adjustment of geodetic networks as a two-dimensional problem in spheroidal
            #   trigonometry, these problems are now solved by three-dimensional methods
            #   (Vincenty & Bowring 1978)[https://www.ngs.noaa.gov/PUBS_LIB/ApplicationOfThreeDimensionalGeodesyToAdjustmentsOfHorizontalNetworks_TM_NOS_NGS13.pdf].
            # computed_position = geod.Direct(float(focus_latitude), float(focus_longitude), bearing, float(total_delta_m))

            # TinyGPS library uses the great-circle distance computation:
            # https://github.com/mikalhart/TinyGPS/blob/db4ef9c97af767e7345f5ccb277ac3bd1a2eb81f/TinyGPS.cpp#L296-L339
            focus = Point(float(focus_latitude), float(focus_longitude))
            computed_position = great_circle(meters=float(total_delta_m)).destination(focus, bearing)

            # Populate results
            res[transmission_payload_tracking_points_delta_km] = delta_d_km
            res[transmission_payload_tracking_points_delta_m] = delta_d_m
            res[transmission_payload_tracking_points_total_delta_m] = total_delta_m
            res[transmission_payload_tracking_points_delta_angle] = bearing
            res[transmission_payload_tracking_points_activity] = activity
            res[transmission_payload_tracking_points_temp_alert] = temp_alert
            res[transmission_payload_tracking_latitude] = computed_position.latitude  # computed_position['lat2']
            res[transmission_payload_tracking_longitude] = computed_position.longitude  # computed_position['lon2']

    elif unpacked[transmission_packet_type] == SCM_DF_Transmission_Payload.SCM_DF_Transmission_Payload_Tracking_v2_0:
        result[transmission_payload] = OrderedDict()
        result[transmission_payload][transmission_payload_tracking_v2_0] = OrderedDict()
        result_tracking_v2_0_payload = result[transmission_payload][transmission_payload_tracking_v2_0]

        tracking_v2_0_payload = unpacked[transmission_payload][transmission_payload_tracking_v2_0]

        # Timestamp
        result_tracking_v2_0_payload[transmission_payload_tracking_days_since_epoch] = \
            tracking_v2_0_payload[transmission_payload_tracking_days_since_epoch]

        # Convert Timeslot
        result_tracking_v2_0_payload[transmission_payload_tracking_timeslot] = \
            tracking_v2_0_payload[transmission_payload_tracking_timeslot] * 2

        # Calculate timestamp
        epoch = datetime.datetime(epoch_year, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
        v2_0_focus_ts = epoch + datetime.timedelta(days=result_tracking_v2_0_payload[transmission_payload_tracking_days_since_epoch], hours=result_tracking_v2_0_payload[transmission_payload_tracking_timeslot])
        result_tracking_v2_0_payload[transmission_payload_tracking_timestamp] = v2_0_focus_ts

        # Convert Longitude
        result_tracking_v2_0_payload[transmission_payload_tracking_longitude] = \
            unpack_signed_int_32(
                tracking_v2_0_payload[transmission_payload_tracking_longitude],
                32 - SCM_DF_TRACKING_V2_0_LONGITUDE_SIZE
            )[0]
        focus_longitude = Decimal(result_tracking_v2_0_payload[transmission_payload_tracking_longitude]) / Decimal(
            SCM_DF_GPS_MULTIPLIER)
        result_tracking_v2_0_payload[transmission_payload_tracking_longitude] = focus_longitude

        # Convert Latitude
        result_tracking_v2_0_payload[transmission_payload_tracking_latitude] = \
            unpack_signed_int_32(
                tracking_v2_0_payload[transmission_payload_tracking_latitude],
                32 - SCM_DF_TRACKING_V2_0_LATITUDE_SIZE
            )[0]
        focus_latitude = Decimal(result_tracking_v2_0_payload[transmission_payload_tracking_latitude]) / Decimal(
            SCM_DF_GPS_MULTIPLIER)
        result_tracking_v2_0_payload[transmission_payload_tracking_latitude] = focus_latitude

        # Convert Orientation
        result_tracking_v2_0_payload[transmission_payload_tracking_orientation] = \
            tracking_v2_0_payload[transmission_payload_tracking_orientation]

        # Convert Activity level
        result_tracking_v2_0_payload[transmission_payload_tracking_activity] = \
            tracking_v2_0_payload[transmission_payload_tracking_activity]

        # Convert Battery voltage
        result_tracking_v2_0_payload[transmission_payload_tracking_battery] = \
            (Decimal(tracking_v2_0_payload[
                         transmission_payload_tracking_battery]) * calculate_v2_0_battery_step()) + SCM_DF_BAT_RANGE_LOW

        # Convert Temperature Min
        result_tracking_v2_0_payload[transmission_payload_tracking_temp_min] = \
            (Decimal(tracking_v2_0_payload[
                         transmission_payload_tracking_temp_min]) * calculate_v2_0_temp_min_step()) + SCM_DF_TEMP_MIN_LOW

        # Convert Temperature Max
        result_tracking_v2_0_payload[transmission_payload_tracking_temp_max] = \
            (Decimal(tracking_v2_0_payload[
                         transmission_payload_tracking_temp_max]) * calculate_v2_0_temp_max_step()) + SCM_DF_TEMP_MAX_LOW

        # Convert Temperature Alert
        result_tracking_v2_0_payload[transmission_payload_tracking_temp_alert] = \
            tracking_v2_0_payload[transmission_payload_tracking_temp_alert] == 1

        # Convert the associated points
        # geod = Geodesic.WGS84
        result_tracking_v2_0_payload[transmission_payload_tracking_points] = []
        result_points = result_tracking_v2_0_payload[transmission_payload_tracking_points]
        for point in tracking_v2_0_payload[transmission_payload_tracking_points]:
            res = OrderedDict()
            result_points.append(res)

            res[transmission_payload_tracking_points_day_offset] = point[transmission_payload_tracking_points_day_offset]
            res[transmission_payload_tracking_points_timeslot] = point[transmission_payload_tracking_points_timeslot] * 2
            point_ts = v2_0_focus_ts - datetime.timedelta(days=point[transmission_payload_tracking_points_day_offset])
            point_ts = point_ts.replace(hour=res[transmission_payload_tracking_points_timeslot])
            res[transmission_payload_tracking_points_timestamp] = point_ts


            # Compute Values
            delta_d_km = point[transmission_payload_tracking_points_delta_km]
            delta_d_m = Decimal(point[transmission_payload_tracking_points_delta_m]) * calculate_v2_0_point_delta_m_step()
            total_delta_m = (delta_d_km * Decimal(1000)) + delta_d_m
            bearing = Decimal(
                point[transmission_payload_tracking_points_delta_angle]) * calculate_v2_0_point_bearing_step()
            activity = point[transmission_payload_tracking_points_activity]
            temp_alert = point[transmission_payload_tracking_points_temp_alert] == 1

            # Geodesy Direct Problem:
            #  https://en.wikipedia.org/wiki/Geodesics_on_an_ellipsoid#Geodesics_on_an_ellipsoid_of_revolution
            #
            # From https://en.wikipedia.org/wiki/Geodesics_on_an_ellipsoid#Applications:
            #   The direct and inverse geodesic problems no longer play the central role in geodesy that they once did.
            #   Instead of solving adjustment of geodetic networks as a two-dimensional problem in spheroidal
            #   trigonometry, these problems are now solved by three-dimensional methods
            #   (Vincenty & Bowring 1978)[https://www.ngs.noaa.gov/PUBS_LIB/ApplicationOfThreeDimensionalGeodesyToAdjustmentsOfHorizontalNetworks_TM_NOS_NGS13.pdf].
            # computed_position = geod.Direct(float(focus_latitude), float(focus_longitude), bearing, float(total_delta_m))

            # TinyGPS library uses the great-circle distance computation:
            # https://github.com/mikalhart/TinyGPS/blob/db4ef9c97af767e7345f5ccb277ac3bd1a2eb81f/TinyGPS.cpp#L296-L339
            focus = Point(float(focus_latitude), float(focus_longitude))
            computed_position = great_circle(meters=float(total_delta_m)).destination(focus, bearing)

            # Populate results
            res[transmission_payload_tracking_points_delta_km] = delta_d_km
            res[transmission_payload_tracking_points_delta_m] = delta_d_m
            res[transmission_payload_tracking_points_total_delta_m] = total_delta_m
            res[transmission_payload_tracking_points_delta_angle] = bearing
            res[transmission_payload_tracking_points_activity] = activity
            res[transmission_payload_tracking_points_temp_alert] = temp_alert
            res[transmission_payload_tracking_latitude] = computed_position.latitude  # computed_position['lat2']
            res[transmission_payload_tracking_longitude] = computed_position.longitude  # computed_position['lon2']


    elif unpacked[transmission_packet_type] == SCM_DF_Transmission_Payload.SCM_DF_Transmission_Payload_Status_v1_0:
        result[transmission_payload] = OrderedDict()
        result[transmission_payload][transmission_payload_status_v1_0] = OrderedDict()
        unpacked_status = unpacked[transmission_payload][transmission_payload_status_v1_0]
        status = result[transmission_payload][transmission_payload_status_v1_0]

        tz = datetime.timezone(
            datetime.timedelta(seconds=unpacked_status[transmission_payload_status_timezone_offset_m] * 60))

        status[transmission_payload_status_timestamp] = datetime.datetime.fromtimestamp(unpacked_status[transmission_payload_status_timestamp], tz)

        status[transmission_payload_status_epoch] = datetime.datetime(
            unpacked_status[transmission_payload_status_epoch], 1, 1, 0, 0, 0, 0, datetime.timezone.utc)

        status[transmission_payload_status_mode] = SCM_DF_Transmission_Status_v1_0_Mode(
            unpacked_status[transmission_payload_status_mode])

        status[transmission_payload_status_timezone] = tz
        status[transmission_payload_status_timezone_offset_m] = unpacked_status[transmission_payload_status_timezone_offset_m]






    # Copy over the BCH32
    for key in [transmission_bch32, transmission_crc16_verified, transmission_bch32_verified]:
        result[key] = unpacked[key]

    result[transmission_decoded_type] = transmission_decoded_raw_type

    return result


def scm_processed_message_decode(message_hex, extra_id=0, service_flag=0, message_counter=0, crc16_ok=True, bch32_ok=True, epoch_year=2023):
    """
    scm_processed_message_decode converts a processed message to the length required by scm_message_decode and then
    calls pad_processed_message on the result. It then populated the SF (service_flag) and MC (message_counter) from the
    passed in parameters.

    :param message_hex: The processed message hex string.
    :param service_flag: The processed message's service_flag field.
    :param message_counter: The processed message's message counter field.
    :param crc16_ok:
    :param bch32_ok:
    :return: An OrderedDict containing the decoded and de-quantized data.
    """

    result = scm_raw_message_decode(pad_processed_message(message_hex), epoch_year)
    result[transmission_id] = extra_id
    result[transmission_SF] = service_flag
    result[transmission_MC] = message_counter

    # We don't have the original
    result[transmission_crc16_verified] = crc16_ok
    result[transmission_bch32_verified] = bch32_ok

    result[transmission_decoded_type] = transmission_decoded_processed_type
    return result


def pad_processed_message(processed_message_hex):
    """
    pad_processed_message takes the stripped down processed_message and add a prefix and suffix of 0x0s to pad the
    message out to the length required by scm_message_decode and then returns the result of calling scm_message_decode
    on the result.
    :param processed_message_hex: the hex string of the processed message
    :return: the processed message padded out to the required (SCM_DF_BUF_SIZE * 8) bits
    """
    if (len(processed_message_hex) * 4) != SCM_DF_BUF_SIZE * 8:
        if (len(processed_message_hex) * 4) == (
                (SCM_DF_BUF_SIZE * 8) - (
                SCM_DF_TRANSMISSION_BCH32_SIZE +
                SCM_DF_TRANSMISSION_CRC16_SIZE +
                SCM_DF_TRANSMISSION_SF_SIZE +
                SCM_DF_TRANSMISSION_MC_SIZE +
                SCM_DF_TRANSMISSION_ID_SIZE
        )
        ):
            processed_message_hex = "{prefix}{message}{suffix}".format(
                prefix="0" * int((
                                         SCM_DF_TRANSMISSION_ID_SIZE +
                                         SCM_DF_TRANSMISSION_CRC16_SIZE +
                                         SCM_DF_TRANSMISSION_SF_SIZE +
                                         SCM_DF_TRANSMISSION_MC_SIZE
                                 ) / 4),
                message=processed_message_hex,
                suffix="0" * int(SCM_DF_TRANSMISSION_BCH32_SIZE / 4)
            )

    ensure_message_length(processed_message_hex)

    return processed_message_hex


def ensure_message_length(message):
    if (len(message) * 4) != SCM_DF_BUF_SIZE * 8:
        raise InvalidMessageSize(
            "Expected message length of {} bytes, received {} bytes.".format(
                SCM_DF_BUF_SIZE, (len(message) / 2)))


def scm_validate_checksums(decoded_message: OrderedDict):
    crc16_calc = get_crc16_calculator()
    bch32_calc = get_bch32_calculator()
    _decoded_message = deepcopy(decoded_message)

    encoded_message = scm_df_encode(_decoded_message)
    bch32_message = encoded_message[:(SCM_DF_BUF_SIZE - int(SCM_DF_TRANSMISSION_BCH32_SIZE / 8))]

    _decoded_message[transmission_crc16] = 0
    encoded_message = scm_df_encode(_decoded_message)
    crc16_message = encoded_message[math.ceil(SCM_DF_TRANSMISSION_ID_SIZE / 8) : SCM_DF_BUF_SIZE - int(SCM_DF_TRANSMISSION_BCH32_SIZE/8)]

    decoded_message[transmission_crc16_verified] = crc16_calc.verify(crc16_message, decoded_message[transmission_crc16])
    decoded_message[transmission_bch32_verified] = bch32_calc.verify(bch32_message, decoded_message[transmission_bch32])
    return decoded_message[transmission_crc16_verified] and decoded_message[transmission_bch32_verified]


class InvalidMessageSize(Exception):
    pass


@lru_cache(maxsize=2)
def calculate_v1_0_battery_step():
    """
    calculate_battery_step calculates the quantized step value for each count of the battery field.
    :return: The step size
    """
    return (SCM_DF_BAT_RANGE_HIGH - SCM_DF_BAT_RANGE_LOW) / (2 ** SCM_DF_TRACKING_V1_0_BATTERY_SIZE)


@lru_cache(maxsize=2)
def calculate_v1_0_temp_max_step():
    """
    calculate_temp_max_step calculates the quantized step value for each count of the temp_min field.
    :return:
    """
    return (SCM_DF_TEMP_MAX_HIGH - SCM_DF_TEMP_MAX_LOW) / (2 ** SCM_DF_TRACKING_V1_0_TEMP_MAX_SIZE)


@lru_cache(maxsize=2)
def calculate_v1_0_temp_min_step():
    """
    calculate_temp_min_step calculates the quantized step value for each count of the temp_min field.
    :return:
    """
    return (SCM_DF_TEMP_MIN_HIGH - SCM_DF_TEMP_MIN_LOW) / (2 ** SCM_DF_TRACKING_V1_0_TEMP_MIN_SIZE)


@lru_cache(maxsize=2)
def calculate_v1_0_point_delta_m_step():
    """
    calculate_point_delta_m_step calculates the quantized step value for each count of the point_delta_m field.
    :return:
    """
    return Decimal('1000') / (2 ** SCM_DF_POINT_V1_0_DELTA_M_SIZE)


@lru_cache(maxsize=2)
def calculate_v1_0_point_bearing_step():
    """
    calculate_point_bearing_step calculates the quantized step value for each count of the point_delta_angle field.
    :return:
    """
    return Decimal('360') / (2 ** SCM_DF_POINT_V1_0_DELTA_ANGLE_SIZE)


@lru_cache(maxsize=2)
def calculate_v2_0_battery_step():
    """
    calculate_battery_step calculates the quantized step value for each count of the battery field.
    :return: The step size
    """
    return (SCM_DF_BAT_RANGE_HIGH - SCM_DF_BAT_RANGE_LOW) / (2 ** SCM_DF_TRACKING_V2_0_BATTERY_SIZE)


@lru_cache(maxsize=2)
def calculate_v2_0_temp_max_step():
    """
    calculate_temp_max_step calculates the quantized step value for each count of the temp_min field.
    :return:
    """
    return (SCM_DF_TEMP_MAX_HIGH - SCM_DF_TEMP_MAX_LOW) / (2 ** SCM_DF_TRACKING_V2_0_TEMP_MAX_SIZE)


@lru_cache(maxsize=2)
def calculate_v2_0_temp_min_step():
    """
    calculate_temp_min_step calculates the quantized step value for each count of the temp_min field.
    :return:
    """
    return (SCM_DF_TEMP_MIN_HIGH - SCM_DF_TEMP_MIN_LOW) / (2 ** SCM_DF_TRACKING_V2_0_TEMP_MIN_SIZE)

@lru_cache(maxsize=2)
def calculate_v2_0_point_delta_m_step():
    """
    calculate_point_delta_m_step calculates the quantized step value for each count of the point_delta_m field.
    :return:
    """
    return Decimal('1000') / (2 ** SCM_DF_POINT_V1_0_DELTA_M_SIZE)

@lru_cache(maxsize=2)
def calculate_v2_0_point_bearing_step():
    """
    calculate_point_bearing_step calculates the quantized step value for each count of the point_delta_angle field.
    :return:
    """
    return Decimal('360') / (2 ** SCM_DF_POINT_V2_0_DELTA_ANGLE_SIZE)


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


if __name__ == "__main__":
    from pprint import pprint

    ## Validate raw message payload decoding
    pprint(scm_raw_message_decode("0EBAA003003845FA9FDB24001ACCC0123CF80006BD700002CDEA00F3BFF5B9", 2023))

    ## Validate processed message decoding
    # message = {
    # "ts": 1682983243409,
    # "values":
    #     {
    #         "msg_date": "2023-05-01T23:20:43.409Z",
    #         "device_id": 184999,
    #         "msg_id": "1102739179156185088",
    #         "RAW_DATA": "000045FB1FDB210000000007840000041E2000032F2400",
    #         "SERVICE_FLAG": 0,
    #         "BCH_STATUS": 1,
    #         "MESSAGE_COUNTER": 60,
    #         "CRC_OK": True,
    #         "checked": "Y"
    #     }
    # }

    # BCH_STATUS = 0
    # result = scm_processed_message_decode(message['values']['RAW_DATA'],
    #                                   extra_id=0,
    #                                   service_flag=0,
    #                                   message_counter=message['values']['MESSAGE_COUNTER'],
    #                                   crc16_ok=message['values']['CRC_OK'],
    #                                   bch32_ok=BCH_STATUS >= 0)
    
    # pprint(result)
