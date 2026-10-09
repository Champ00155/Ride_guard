import os
import time

RFCOMM_DEVICE = "/dev/rfcomm0"


def send(command):
    command = command.strip().upper()

    if command not in ("LEFT", "RIGHT", "OFF"):
        raise ValueError(f"Invalid haptic command: {command}")

    if not os.path.exists(RFCOMM_DEVICE):
        raise RuntimeError(
            f"{RFCOMM_DEVICE} not found. "
            "Run ./connect_esp32.sh first."
        )

    with open(RFCOMM_DEVICE, "w") as bluetooth:
        bluetooth.write(command + "\n")
        bluetooth.flush()

    print(f"HAPTIC → {command}")


if __name__ == "__main__":

    print("RIDEGUARD HAPTIC TEST")
    print("---------------------")

    send("LEFT")
    time.sleep(2)

    send("RIGHT")
    time.sleep(2)

    send("OFF")

    print("Haptic test complete.")
