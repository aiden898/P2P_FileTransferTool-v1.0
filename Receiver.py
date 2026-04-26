import socket
import threading
import os
import zipfile

DISCOVERY_PORT = 5000
FILE_PORT = 5001
BUFFER_SIZE = 4096

DEVICE_NAME = "P2P-Receiver"

# Toggle: auto extract folders
AUTO_EXTRACT = True



#  DISCOVERY RESPONDER

def discovery_responder():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("", DISCOVERY_PORT))

    print("[Receiver] Discovery running...")

    while True:
        try:
            data, addr = s.recvfrom(1024)

            if data.decode() == "DISCOVER":
                s.sendto(f"{DEVICE_NAME}|{FILE_PORT}".encode(), addr)

        except:
            pass



#  FILE RECEIVER

def file_receiver():
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("", FILE_PORT))
    s.listen(1)

    print(f"[Receiver] Listening on {FILE_PORT}...")

    while True:
        conn, addr = s.accept()
        print(f"\n[Receiver] Connected: {addr}")

        try:
            meta = conn.recv(1024).decode()
            filename, filesize = meta.split("|")
            filesize = int(filesize)

            save_name = "recv_" + filename
            received = 0

            with open(save_name, "wb") as f:
                while received < filesize:
                    data = conn.recv(BUFFER_SIZE)
                    if not data:
                        break

                    f.write(data)
                    received += len(data)

                    print(f"\rReceiving... {(received/filesize)*100:.1f}%", end="")

            print(f"\nSaved: {save_name}")

           
            #  AUTO EXTRACT
           
            if AUTO_EXTRACT and save_name.endswith(".zip"):
                extract_folder = save_name.replace(".zip", "_extracted")

                os.makedirs(extract_folder, exist_ok=True)

                with zipfile.ZipFile(save_name, "r") as z:
                    z.extractall(extract_folder)

                print(f" Auto-extracted to: {extract_folder}")

        except Exception as e:
            print("[Receiver Error]", e)

        finally:
            conn.close()

#  START

def main():
    print("=== P2P Receiver v1.3===")

    threading.Thread(target=discovery_responder, daemon=True).start()
    threading.Thread(target=file_receiver, daemon=True).start()

    print("[Receiver] Ready...\n")

    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("\n[Receiver] Stopping...")


if __name__ == "__main__":
    main()
