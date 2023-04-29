# SCM Utils
SCM_Utils is a library of utilities for the Space Cows Project

## ToDo
Thing left to do:

  - [ ] Validate the computed positions
  - [ ] Deal with the over-precision of the computer positions.

## Install
```bash
$ pip install git+https://github.com/jcu-eresearch/SCM_Utils.git
```

## Usage

```python
from scm.utils.scm_msg import scm_message_decode

result = scm_message_decode("0EBAA003003845FA9FDB24001ACCC0123CF80006BD700002CDEA00F3BFF5B9")
```