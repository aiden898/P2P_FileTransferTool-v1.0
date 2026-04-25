import socket
import threading
import os

DISCOVERY_PORT = 5000
FILE_PORT = 5001
BUFFER_SIZE = 4096

DEVICE_NAME = "P2P-Receiver"

# DISCOVERY RESPONDER

def discovery_responder():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("", DISCOVERY_PORT))

    print("[Receiver] Discovery responder running...")

    while True:
        data, addr = s.recvfrom(1024)

        if data.decode() == "DISCOVER":
            response = f"{DEVICE_NAME}|{FILE_PORT}"
            s.sendto(response.encode(), addr)

# FILE RECEIVER

def file_receiver():
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("", FILE_PORT))
    s.listen(1)

    print(f"[Receiver] Listening for file transfers on port {FILE_PORT}...")

    while True:
        conn, addr = s.accept()
        print(f"[Receiver] Connection from {addr}")

        try:
            # Receive metadata
            meta = conn.recv(1024).decode()
            filename, filesize = meta.split("|")
            filesize = int(filesize)

            print(f"[Receiver] Receiving: {filename} ({filesize} bytes)")

            # Save file safely
            save_name = "recv_" + filename
            received = 0

            with open(save_name, "wb") as f:
                while received < filesize:
                    data = conn.recv(BUFFER_SIZE)
                    if not data:
                        break

                    f.write(data)
                    received += len(data)

                    percent = (received / filesize) * 100
                    print(f"\r[Receiver] {percent:.1f}% complete", end="")

            print(f"\n[Receiver] Saved as: {save_name}")

        except Exception as e:
            print("[Receiver] Error:", e)

        finally:
            conn.close()

# START RECEIVER

def main():
    print("=== P2P Receiver Starting ===")

    threading.Thread(target=discovery_responder, daemon=True).start()
    threading.Thread(target=file_receiver, daemon=True).start()

    print("[Receiver] Ready and waiting...\n")

    # Keep main thread alive
    while True:
        pass


if __name__ == "__main__":
    main()
