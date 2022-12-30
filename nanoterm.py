import os
import select
import sys
import tty
print("\033[?25l\033[?1c")
import famebruffer
import subprocess

if __name__ == "__main__":
	#master_fd, child_fd = os.openpty()
	p_pid, master_fd = os.forkpty()
	if p_pid == 0:  # Child.
		#os.close(master_fd)

		#os.setsid()

		#os.dup2(child_fd,0)
		#os.dup2(child_fd,1)
		#os.dup2(child_fd,2)
		#os.close(child_fd)

		os.execle("/bin/zsh","/bin/zsh",{"TERM":"xterm-256color","COLUMNS":str(1920//6),"LINES":str(1080//12)})
		#a = subprocess.Popen("weechat",stdin=sys.stdin,stdout=master_fd)

	if p_pid > 0:
		tty.setcbreak(0)
		while True:
			try: [_master_fd], _wlist, _xlist = select.select([master_fd],[],[],0)
			except ValueError:
				pass
			else:
				data = os.read(master_fd,2048)
				print(data,file=sys.stderr)
				sys.stdout.write(str(data,"utf-8",errors="ignore"))
			
			if len(select.select([0],[],[],0)[0]) > 0:
				indata = os.read(0,2048)
				os.write(master_fd,indata)
