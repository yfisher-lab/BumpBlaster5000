import subprocess


class FictracProcess:

    def __init__(self,
                 fictrac_path=r'C:\Users\fisherlab\Documents\FicTrac211\fictrac.exe',
                 config_file=r'C:\Users\fisherlab\Documents\FicTrac211\config.txt'):
        self.fictrac_path = fictrac_path
        self.config_file = config_file
        self.p = None

    def open(self, creationflags=subprocess.CREATE_NEW_CONSOLE):
        self.p = subprocess.Popen([self.fictrac_path, self.config_file], creationflags=creationflags)

    def close(self):
        self.p.kill()
        self.p.terminate()
        self.p = None