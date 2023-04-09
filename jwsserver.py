import threading
import socket
import pickle
import subprocess
import io
from PIL import Image
import atexit
from tkinter import messagebox
from mttkinter.mtTkinter import Tk, Toplevel
import ttkbootstrap as tkinter
import mss
import ctypes

ctypes.windll.shcore.SetProcessDpiAwareness(1)
ScaleFactor = ctypes.windll.shcore.GetScaleFactorForDevice(0)


@atexit.register
def _():
    messagebox.showerror("Error", "You can not close it!")


class Setting:
    from time import sleep

    @staticmethod
    def wait():
        Setting.sleep(0.05)

    MAXN = (1 << 31) - 1
    PORT = 518
    HOST = socket.gethostbyname(socket.gethostname())


__all__ = ["Handle"]


class Handle:
    def __init__(self, label, win):
        self.record = [(0, "_INIT", 0)]
        self.label = label
        self.win: Tk = win

    def main(self, msg) -> int:
        flag = msg[0]
        value = msg[1]
        v = -1
        if flag == "command":
            v = self.command(value)
        elif flag == "transfer":
            v = self.transfer(value)
        elif flag == "control":
            v = self.control(value)
        self.record.append((len(self.record), flag, v))
        return v

    def command(self, value) -> str:
        exe = subprocess.Popen(value, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        v = exe.communicate()[0].decode("ansi")
        return v

    def transfer(self, value) -> str:
        with open(value[1], "wb") as f:
            f.write(value[0])
        return "OK"

    def control(self, value) -> str:
        v = value.split(" ")
        if len(v) == 2:
            if v[0] == "Y":
                self.win.deiconify()
                self.win.tk.call('tk', 'scaling', ScaleFactor)
                self.win.attributes('-topmost', True)
                self.win.attributes('-fullscreen', True)
            else:
                self.win.withdraw()
            self.label.set(v[1])
            return "OK"
        else:
            return "Parameter Error"


class JWSServer:
    def __init__(self):
        self.s1 = socket.socket()
        self.s2 = socket.socket()
        self.s1.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s2.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.host1 = (Setting.HOST, Setting.PORT)
        self.host2 = (Setting.HOST, Setting.PORT + 1)
        self.main()
        tk = Tk()
        tk.withdraw()
        self.tk = Toplevel()
        self.tk.withdraw()
        self.tk_value = tkinter.StringVar(self.tk)
        value = tkinter.Label(self.tk, textvariable=self.tk_value, font=("宋体", 120))
        value.pack(side='top', expand='yes')
        tk.mainloop()

    def main(self):
        threading.Thread(target=self._main_1).start()
        threading.Thread(target=self._main_2).start()

    def _main_2(self):
        self.s2.bind(self.host2)
        self.s2.listen(Setting.MAXN)
        while True:
            client, addr = self.s2.accept()
            thread = threading.Thread(target=self.handle2, args=(client,), name=f"JWS CONNECT {addr[0]} (2)")
            thread.setDaemon(True)
            thread.start()

    def handle2(self, client: socket.socket):
        with mss.mss() as sct:
            while client:
                byte_value = io.BytesIO()
                try:
                    rect = sct.monitors[1]
                    picture = sct.grab(rect)

                    img = Image.new("RGB", picture.size)
                    img.frombytes(picture.rgb)
                    img = img.resize((114 * 5, 90 * 5))
                except OSError:
                    img = Image.new("RGB", (114 * 5, 90 * 5), (0, 0, 0))
                img.save(byte_value, format='PNG')
                try:
                    client.send(byte_value.getvalue())
                    Setting.wait()
                    v = client.recv(Setting.MAXN)
                    Setting.wait()
                    if not v:
                        break
                except (ConnectionError, OSError):
                    client.close()

    def _main_1(self):
        self.s1.bind(self.host1)
        self.s1.listen(Setting.MAXN)
        while True:
            client, addr = self.s1.accept()
            thread = threading.Thread(target=self.handle1, args=(client,), name=f"JWS CONNECT {addr[0]} (2)")
            thread.setDaemon(True)
            thread.start()

    def handle1(self, client: socket.socket):
        qst = Handle(self.tk_value, self.tk)
        while client:
            try:
                v = client.recv(Setting.MAXN)
            except ConnectionResetError:
                break
            msg = pickle.loads(v)
            client.send(pickle.dumps(qst.main(msg)))


if __name__ == '__main__':
    s = JWSServer()
