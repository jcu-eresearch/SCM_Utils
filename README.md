# SCM Utils

SCM_Utils is a library of utilities for the Space Cows Project

## ToDo

Thing left to do:

- [ ] Validate the computed positions.
- [ ] Deal with the over-precision of the computed positions.
- [ ] Migrate to the new message format.
- [x] Handle processed messages
- [x] Verify checksums on raw messages

## Install

```bash
$ pip install git+https://github.com/jcu-eresearch/SCM_Utils.git
```

## Usage

### Decode a Raw Message Hex String

```python
from scm.utils.scm_msg import scm_message_decode

result = scm_message_decode("013a4049000045fb1fdb210000000007840000041e2000032f2400002e2930")
```

### Decode a Processed Message Hex String

```python
from scm.utils.scm_msg import scm_processed_message_decode

result = scm_processed_message_decode("000045FB1FDB210000000007840000041E2000032F2400",
                                      extra_id=0,
                                      service_flag=0,
                                      message_counter=73,
                                      crc16_ok=True,
                                      bch32_ok=True)
```

Where result is:

```python
OrderedDict(
    [
        ('id', 0),
        ('crc16', 0),
        ('SF', 0),
        ('MC', 73),
        ('packet_type', < SCM_DF_Transmission_Payload.SCM_DF_Transmission_Payload_Tracking: 0 >),
        ('payload',
         OrderedDict(
             [
                 ('tracking',
                  OrderedDict(
                      [
                          ('flags', 0),
                          ('timeslot', 0),
                          ('longitude', Decimal('146.75968')),
                          ('latitude', Decimal('-19.331072')),
                          ('orientation', 0), ('activity', 0),
                          ('battery', Decimal('3.00')),
                          ('temp_min', Decimal('0.0')),
                          ('temp_max', Decimal('20.0')),
                          ('temp_alert', False),
                          ('points',
                           [
                               OrderedDict(
                                   [
                                       ('delta_km', 0),
                                       ('delta_m', Decimal('234.3750')),
                                       ('total_delta_m', Decimal('234.3750')),
                                       ('delta_angle', Decimal('22.50000000')),
                                       ('activity', 0),
                                       ('temp_alert', False),
                                       ('latitude', -19.32912466132596),
                                       ('longitude', 146.76053479568455)]
                               ),
                               OrderedDict(
                                   [
                                       ('delta_km', 0),
                                       ('delta_m', Decimal('250.0000')),
                                       ('total_delta_m', Decimal('250.0000')),
                                       ('delta_angle', Decimal('338.90625000')),
                                       ('activity', 0),
                                       ('temp_alert', False),
                                       ('latitude', -19.3289743495036),
                                       ('longitude', 146.75882251438833)]
                               ),
                               OrderedDict(
                                   [
                                       ('delta_km', 0),
                                       ('delta_m', Decimal('390.6250')),
                                       ('total_delta_m', Decimal('390.6250')),
                                       ('delta_angle', Decimal('340.66406250')),
                                       ('activity', 0),
                                       ('temp_alert', False),
                                       ('latitude', -19.32775718029063),
                                       ('longitude', 146.75844736292584)
                                   ]
                               )
                           ])
                      ]
                  ))
             ]
         )),
        ('bch32', 0),
        ('crc16_verified', True),
        ('bch32_verified', True),
        ('decode_type', 'processed')
    ]
)
```