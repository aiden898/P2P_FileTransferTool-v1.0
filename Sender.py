import socket
import os
import time

DISCOVERY_PORT = 5000
BUFFER_SIZE = 4096


# Scan for devices
def scan_devices():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    s.settimeout(2)

    s.sendto(b"DISCOVER", ("255.255.255.255", DISCOVERY_PORT))

    devices = []

    try:
        while True:
            data, addr = s.recvfrom(1024)
            name, port = data.decode().split("|")

            # Avoid duplicates
            if not any(d[1] == addr[0] for d in devices):
                devices.append((name, addr[0], int(port)))
    except socket.timeout:
        pass

    return devices


# Send file
def send_file(ip, port, filepath):
    if not os.path.exists(filepath):
        print("File not found Error")
        return

    filesize = os.path.getsize(filepath)
    filename = os.path.basename(filepath)

    s = socket.socket()
    s.connect((ip, port))

    # Send metadata
    s.send(f"{filename}|{filesize}".encode())
    time.sleep(0.1)

    sent = 0

    with open(filepath, "rb") as f:
        while chunk := f.read(BUFFER_SIZE):
            s.sendall(chunk)
            sent += len(chunk)

            percent = (sent / filesize) * 100
            print(f"\rSending... {percent:.1f}%", end="")

    print("\nTransfer complete")
    s.close()


# CLI Menu
def menu():
    while True:
        print("\n=== P2P File Transfer v1.0 ===")
        print("1. Scan for devices")
        print("2. Exit")

        choice = input("> ")

        if choice == "1":
            print("Scanning...")
            devices = scan_devices()

            if not devices:
                print("No devices found Error")
                continue

            print("\nAvailable Devices:")
            for i, d in enumerate(devices):
                print(f"{i+1}. {d[0]} ({d[1]}:{d[2]})")

            try:
                selection = int(input("\nSelect device #: ")) - 1
                device = devices[selection]
            except:
                print("Invalid selection Error")
                continue

            filepath = input("Enter file path: ").strip()

            send_file(device[1], device[2], filepath)

        elif choice == "2":
            print("Exiting...")
            break

        else:
            print("Invalid option Error")


if __name__ == "__main__":
    menu()
