# Recovery

## Lost Admin Password

The admin password salt and repeated password hash are stored in `settings.py` on the Pico. Runtime bearer tokens are not stored there.

To reset the device:

1. Connect the Pico over USB in a controlled physical environment.
2. Delete `/settings.py` from the Pico filesystem.
3. Restart the Pico.
4. Open `http://PICO_IP/setup`.
5. Create a new admin password.

Deleting `settings.py` intentionally returns the device to first-run setup.

## Suspected Physical Tamper

Treat physical tamper as full credential compromise.

Do this after any suspected physical access:

- delete `settings.py`
- create a new admin password
- restart the app so new runtime tokens are generated
- verify the project files on the Pico match the repository
- inspect the enclosure, USB data exposure, BOOTSEL access, reset access, and SWD pins

## Deployment Control

For stronger physical security:

- put the Pico inside a locked enclosure
- do not expose USB data
- do not expose BOOTSEL, reset, or SWD pins
- use tamper-evident seals
- power the Pico from an internal controlled supply

A standard Raspberry Pi Pico does not provide secure boot or flash encryption, so physical access cannot be made fully secure by firmware alone.
