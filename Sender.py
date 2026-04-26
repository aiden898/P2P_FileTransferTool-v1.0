import socket
import os
import time
import zipfile
import tempfile

DISCOVERY_PORT = 5000
BUFFER_SIZE = 4096

# v.1.3- added folder support, progress bar, ETA, and speed display

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

            if not any(d[1] == addr[0] for d in devices):
                devices.append((name, addr[0], int(port)))
    except socket.timeout:
        pass

    return devices



def zip_folder(folder_path):
    temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    temp_zip.close()

    with zipfile.ZipFile(temp_zip.name, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                full = os.path.join(root, file)
                arc = os.path.relpath(full, folder_path)
                zipf.write(full, arc)

    return temp_zip.name


def draw_progress(percent, speed, eta, width=30):
    filled = int(width * percent / 100)
    bar = "█" * filled + "-" * (width - filled)

    print(
        f"\r[{bar}] {percent:6.2f}% "
        f"| {speed:6.2f} MB/s "
        f"| ETA: {eta:5.1f}s",
        end=""
    )


def send_file(ip, port, filepath):
    if not os.path.exists(filepath):
        print("❌ File/Folder not found")
        return

    temp_zip = None

    try:
        # folder → zip
        if os.path.isdir(filepath):
            print("Folder detected → compressing...")
            filepath = zip_folder(filepath)
            temp_zip = filepath
            print("Compression done")

        filesize = os.path.getsize(filepath)
        filename = os.path.basename(filepath)

        print(f"\nSending: {filename}")
        print(f"Size: {filesize / (1024*1024):.2f} MB\n")

        s = socket.socket()
        s.connect((ip, port))

        s.send(f"{filename}|{filesize}".encode())
        time.sleep(0.1)

        sent = 0
        start_time = time.time()

        speed_history = []

        with open(filepath, "rb") as f:
            while chunk := f.read(BUFFER_SIZE):
                s.sendall(chunk)
                sent += len(chunk)

                # =========================
                #  TIME + SPEED
                # =========================
                elapsed = time.time() - start_time

                speed = (sent / (1024 * 1024)) / elapsed if elapsed > 0 else 0

                # smooth speed (moving average)
                speed_history.append(speed)
                if len(speed_history) > 10:
                    speed_history.pop(0)

                smooth_speed = sum(speed_history) / len(speed_history)

                remaining = filesize - sent
                eta = (remaining / (smooth_speed * 1024 * 1024)) if smooth_speed > 0 else 0

                percent = (sent / filesize) * 100

                draw_progress(percent, smooth_speed, eta)

        print("\n\nTransfer complete")

    except Exception as e:
        print(f"\nError: {e}")

    finally:
        if temp_zip and os.path.exists(temp_zip):
            os.remove(temp_zip)
            print("🧹 Temp zip removed")



#  MENU

def menu():
    while True:
        print("\n=== P2P File Transfer v1.3===")
        print("1. Scan for devices")
        print("2. Exit")

        choice = input("> ")

        if choice == "1":
            print("Scanning...")
            devices = scan_devices()

            if not devices:
                print("No devices found")
                continue

            print("\nAvailable Devices:")
            for i, d in enumerate(devices):
                print(f"{i+1}. {d[0]} ({d[1]}:{d[2]})")

            try:
                idx = int(input("\nSelect device #: ")) - 1
                device = devices[idx]
            except:
                print("Invalid selection")
                continue

            path = input("File or folder path: ").strip('"')

            send_file(device[1], device[2], path)

        elif choice == "2":
            print("Exiting...")
            break

        else:
            print("Invalid option")


if __name__ == "__main__":
    menu()
