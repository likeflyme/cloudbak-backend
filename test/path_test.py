import os.path
from pathlib import Path

path_a = "D:\\workspace\\sessions\\6\\wxid_x1j6ne5cnl8r19"
path_b = "Msg\\Applet.db"
print(os.path.join(path_a, path_b))
print(Path(path_a))
