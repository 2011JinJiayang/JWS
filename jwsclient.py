import tkinter as tk
from tkinter import messagebox, filedialog
import ttkbootstrap as tkinter
from socket import gethostbyname, gethostname
import threading
import socket
import pickle
import io
from PIL import Image, ImageTk
from typing import List


class Setting:
    from time import sleep, ctime
    from os import _exit as exit

    @staticmethod
    def wait():
        Setting.sleep(0.05)

    MAXN = (1 << 31) - 1
    PORT = 518
    HOST = socket.gethostbyname(socket.gethostname())

    @staticmethod
    def CLOCK():
        return Setting.ctime().split()[3]


class JWSClient:
    def __init__(self):
        self.s = socket.socket()
        self.host = ("127.0.0.1", Setting.PORT)

    def main(self, host):
        client_queue.append(self)
        self.host = (host, Setting.PORT)
        self.s.connect(self.host)
        LOG.write(f"{host} 连接成功")

    def send(self, value):
        if value[0] == "transfer":
            value[1] = value[1].split(" ")
            with open(value[1][0], "rb") as f:
                value[1][0] = f.read()
        v = pickle.dumps(value)
        self.s.send(v)
        return pickle.loads(self.s.recv(Setting.MAXN))


client_queue: List[JWSClient] = []


class JWSPictureClient:
    def __init__(self, gui):
        self.image = gui
        self.s = socket.socket()
        self.host = ("127.0.0.1", Setting.PORT + 1)

    def main(self, host):
        thread = threading.Thread(target=self._main, args=(host,))
        thread.setDaemon(True)
        thread.start()

    def _main(self, host):
        self.host = (host, Setting.PORT + 1)
        self.s.connect(self.host)
        while True:
            get = self.s.recv(Setting.MAXN)
            Setting.wait()
            byte_value = io.BytesIO(get)
            img = Image.open(byte_value)
            imgtk = ImageTk.PhotoImage(img)
            self.image.configure(image=imgtk)
            self.s.send(b"OK")
            Setting.wait()

    def send(self, value):
        if value[0] == "transfer":
            value[1] = value[1].split(" ")
            with open(value[1][0], "rb") as f:
                value[1][0] = f.read()
        v = pickle.dumps(value)
        self.s.send(v)
        return pickle.loads(self.s.recv(Setting.MAXN))


class Page(tkinter.Frame):
    def __init__(self):
        self.name = ""
        super(Page, self).__init__()

    def init(self, name):
        self.name = name
        app.add(self.name, self)
        app.select(self)


class Logging:
    class __Log(tkinter.Text):
        def __init__(self, obj, parent, **kw):
            super().__init__(parent, state=tkinter.DISABLED, **kw)
            self.obj = obj

        def write(self, obj, value):
            if obj is self.obj:
                self.config(state=tkinter.NORMAL)
                message.set(value.split("\n")[0])
                self.insert("end", value)
                self.config(state=tkinter.DISABLED)

    def __init__(self):
        self.__value = ""
        self.__tks: List[self.__Log] = []
        self.__time = 0

    def write(self, _v):
        self.__time += 1
        _v = f"[{self.__time}][{Setting.CLOCK()}] {_v}\n"
        self.__value += _v
        for log in self.__tks:
            log.write(self, _v)

    def tk(self, parent, **kw):
        log = self.__Log(self, parent, **kw)
        self.__tks.append(log)
        return log


class Control(Page):
    def __init__(self):
        super(Control, self).__init__()

        self.logging = LOG.tk(self, width=163, height=24)
        self.logging.grid(row=1, column=1)
        frame1 = tkinter.Frame(self)
        self.get1 = tkinter.Variable(value=gethostbyname(gethostname()))
        e = tkinter.Entry(frame1, textvariable=self.get1, width=120)
        e.bind("<Return>", self.connect)
        e.grid(row=1, column=1)
        tk.Button(frame1, text="连接……", command=self.connect, width=42).grid(row=1, column=2)
        frame1.grid(row=2, column=1)
        tk.Label(self, textvariable=message, width=163, anchor="e").grid(row=3, column=1)

    def connect(self, event=None):
        host = self.get1.get()
        Client(host)


class CentralClient(Page):
    __option__ = ["command", "transfer", "exit", "control"]

    def __init__(self):
        super(CentralClient, self).__init__()
        self.flag = tkinter.IntVar(value=0)
        self.result = None
        frame = tkinter.Frame(self)
        frame.grid(row=1, column=1)
        self.text = tkinter.ScrolledText(frame, width=160, height=20, state=tkinter.DISABLED)
        self.text.grid(row=1, column=1, columnspan=2)
        self.type = tkinter.Variable()
        opt = tkinter.OptionMenu(
            frame, self.type, "command", *self.__option__)
        opt.config(width=18)
        opt.grid(row=2, column=1)
        self.value = tkinter.ScrolledText(frame, width=135, height=5)
        self.value.grid(row=2, column=2, rowspan=2)
        self.time = 0
        tk.Button(frame, text="运行", command=self.calc, width=24, height=3).grid(row=3, column=1)
        self.message = tkinter.StringVar(self)
        tkinter.Label(self, textvariable=self.message, width=164, anchor="e").grid(row=2, columnspan=2, column=1)

    def calc(self):
        for i in client_queue:
            def func():
                i.send([t, v])

            t = self.type.get()
            if t == "exit":
                LOG.write(f"全体用户 解除连接")
                Setting.exit(0)
                return None
            v = self.value.get("1.0", "end").rstrip().lstrip()
            thread = threading.Thread(target=func)
            thread.setDaemon(True)
            thread.start()
        LOG.write(f"全体用户 运行命令 {t}:\"{v}\" 成功")


class Client(Page):
    __option__ = ["command", "transfer", "exit", "control"]

    def connect(self, ip):
        try:
            self.client.main(ip)
        except OSError:
            messagebox.showerror("地址无效", "该地址无效或无法响应JWS服务")
            app.delete(self)

    def __init__(self, ip):
        super(Client, self).__init__()
        self.client = JWSClient()
        thread = threading.Thread(target=self.connect, args=(ip,))
        thread.setDaemon(True)
        thread.start()
        self.flag = tkinter.IntVar(value=0)
        self.result = None
        frame = tkinter.Frame(self)
        frame.grid(row=1, column=1)
        self.text = tkinter.ScrolledText(frame, width=79, height=20, state=tkinter.DISABLED)
        self.text.grid(row=1, column=1, columnspan=2)
        self.type = tkinter.Variable()
        opt = tkinter.OptionMenu(
            frame, self.type, "command", *self.__option__)
        opt.config(width=17)
        opt.grid(row=2, column=1)
        self.value = tkinter.ScrolledText(frame, width=55, height=5)
        self.value.grid(row=2, column=2, rowspan=2)
        self.time = 0
        tk.Button(frame, text="运行", command=self.calc, width=23, height=3).grid(row=3, column=1)
        label = tkinter.Label(self)
        label.grid(row=1, column=2)
        self.message = tkinter.StringVar(self)
        tkinter.Label(self, textvariable=self.message, width=164, anchor="e").grid(row=2, columnspan=2, column=1)
        self.picture_client = JWSPictureClient(label)
        self.picture_client.main(ip)
        self.init(ip)
        self.ip = ip

    def calc(self):
        def func():
            self.result = self.client.send([t, v])
            self.flag.set(0)

        t = self.type.get()
        if t == "exit":
            LOG.write(f"{self.ip} 解除连接")
            app.delete(self)
            client_queue.remove(self.client)
            return None
        v = self.value.get("1.0", "end").rstrip().lstrip()
        thread = threading.Thread(target=func)
        thread.setDaemon(True)
        thread.start()
        self.wait_variable(self.flag)
        self.time += 1
        self.text.config(state=tkinter.NORMAL)
        self.text.insert("end", f"[{self.time} {t}: \"{v}\"] {self.result}\n")
        self.message.set(f"[{self.time} {t}: \"{v}\"] {self.result}".split("\n")[0])
        self.text.config(state=tkinter.DISABLED)
        LOG.write(f"{self.ip} 运行命令 {t}:\"{v}\" 成功")


class JWSRecordRunner:
    def __init__(self, string):
        self.code = string.split("\n")
        self.special = {
            "LOCALHOST": lambda: socket.gethostbyname(socket.gethostname()),
        }
        self.cdp = 1
        self.client = None
        thread = threading.Thread(target=self.run)
        thread.setDaemon(True)
        thread.start()

    def run(self):
        while self.cdp <= len(self.code):
            if self.code[self.cdp-1]:
                self.do(self.code[self.cdp-1])
            self.cdp += 1

    def do(self, value: str):
        v = self.split(value)
        if v[0] == "Connect":
            if v[1] in self.special:
                v[1] = self.special[v[1]]()
            self.client = Client(v[1]).client
        elif v[0] == "Run":
            if self.client is None:
                self.error(f"第{self.cdp}行：客户端未连接")
            self.client.send([v[1], v[2]])
        elif v[0] == "Delay":
            Setting.sleep(float(int(v[1])))
        elif v[0] == "Jump":
            self.cdp = v[1]
        elif v[0] == "Exit":
            self.cdp = len(self.code)+1

    def error(self, msg):
        messagebox.showerror(msg)

    def split(self, value: str):
        chars = ""
        result = []
        for i in value:
            if i == " " and len(result) < 2:
                result.append(chars)
                chars = ""
            else:
                chars += i
        if chars:
            result.append(chars)
        return result


class Tool:
    def open(self):
        file = filedialog.askopenfilename(filetypes=[("*.jws", "JWS Record")])
        if file:
            with open(file, "r", encoding="utf-8") as f:
                JWSRecordRunner(f.read())


class App:
    def __init__(self):
        self.win = tk.Tk()
        self.win.title("JWS Client")
        self.win.attributes("-alpha", 0.98)
        self.win.resizable(False, False)
        self.tool = Tool()
        self.win.config(menu=self.menu())
        self.app = tkinter.Notebook(self.win)
        self.app.enable_traversal()
        self.app.grid()

    def menu(self):
        menu = tkinter.Menu()
        file_menu = tkinter.Menu(menu, tearoff=False)
        file_menu.add_command(label="打开", command=self.tool.open)
        menu.add_cascade(menu=file_menu, label="文件")
        return menu

    def main(self):
        self.win.mainloop()

    def add(self, name, page):
        self.app.add(page, text=name)

    def delete(self, page):
        self.app.forget(page)

    def select(self, page):
        self.app.select(page)


if __name__ == '__main__':
    app = App()
    message = tkinter.StringVar()
    LOG = Logging()
    _ = Control()
    _.init("Control")
    CentralClient().init("CentralClient")
    app.select(_)
    app.main()
