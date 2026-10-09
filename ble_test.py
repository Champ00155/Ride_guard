import asyncio
from bleak import BleakScanner, BleakClient


# ========================================
# RIDEGUARD BLE CONFIGURATION
# ========================================

DEVICE_NAME = "RIDEGUARD-ESP32"

SERVICE_UUID = "12345678-1234-1234-1234-123456789001"

CHARACTERISTIC_UUID = "12345678-1234-1234-1234-123456789002"


# ========================================
# FIND ESP32
# ========================================

async def find_esp32():

    print("Scanning for RIDEGUARD-ESP32...")
    print("Keep the ESP32 powered on.")
    print()

    devices = await BleakScanner.discover(timeout=8)

    for device in devices:

        print(
            f"Found: {device.name} "
            f"[{device.address}]"
        )

        if device.name == DEVICE_NAME:

            print()
            print("RIDEGUARD ESP32 FOUND!")
            return device

    return None


# ========================================
# SEND BLE COMMAND
# ========================================

async def send_command(command):

    device = await find_esp32()

    if device is None:

        print()
        print("ERROR: RIDEGUARD-ESP32 not found.")
        return

    print()
    print(f"Connecting to {DEVICE_NAME}...")

    async with BleakClient(device) as client:

        print("Connected!")

        print(f"Sending command: {command}")

        await client.write_gatt_char(
            CHARACTERISTIC_UUID,
            command.encode("utf-8"),
            response=False
        )

        print("Command sent successfully!")


# ========================================
# MAIN
# ========================================

async def main():

    print()
    print("==============================")
    print(" RIDEGUARD BLE TEST")
    print("==============================")
    print()

    print("Commands:")
    print("  L = LEFT")
    print("  R = RIGHT")
    print("  O = OFF")
    print("  Q = QUIT")
    print()

    while True:

        command = input("Enter command: ").strip().upper()

        if command == "L":

            await send_command("LEFT")

        elif command == "R":

            await send_command("RIGHT")

        elif command == "O":

            await send_command("OFF")

        elif command == "Q":

            print("Exiting...")
            break

        else:

            print("Invalid command.")
            print("Use L, R, O, or Q.")

        print()


if __name__ == "__main__":
    asyncio.run(main())
