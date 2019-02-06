#!/usr/bin/env python

import argparse
import os
from pyfiglet import figlet_format
from termcolor import cprint, colored
import subprocess
import sys

cprint(figlet_format("Tuneladora SSH"), "green", attrs=["bold"])

cprint("Tuneladora SSH 0.6\nA SSH port redirector for lazy people (made with love by tonikelope).", attrs=["bold"])

parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=colored("\n#1")+colored(" tuneladora 192.168.1.5 'localhost#localhost#8080->8080'", "green")+colored(" (Redirects local port 8080 of (local) localhost to remote port 8080 of (remote) localhost on remote machine 192.168.1.5)")+colored("\n\n#2")+colored(" tuneladora 192.168.1.5 8080", "green")+colored(" (Same as #1)")+colored("\n\n#3")+colored(" tuneladora 192.168.1.5 '8080:8081'", "green")+colored(" (Redirects local ports 8080 to 8081 of (local) localhost to remote ports 8080 to 8081 of (remote) localhost on remote machine 192.168.1.5)")+colored("\n\n#4")+colored(" tuneladora 192.168.1.5 '8080:8081,9000->10000'", "green")+colored(" (Redirects local ports 8080 to 8081 and 9000 of (local) localhost to remote ports 8080 to 8081 and 10000 of (remote) localhost on remote machine 192.168.1.5)"))

parser.add_argument("destination", help="Destination host.")

parser.add_argument("ports", help="[[local_address#]<remote_address#>]<lport[->rport]|lport_range_init:lport_range_end[,...]>[+...]")

parser.add_argument('--proxy', help='ssh -o ProxyCommand=')

args = parser.parse_args()

ssh_command_line = "ssh -N"

try:
	max_open_files = int(subprocess.check_output(["ulimit -n"], shell=True).decode())
except:
	max_open_files = None

tot_open_files = 0

if args.proxy:
	ssh_command_line=ssh_command_line+" -o ProxyCommand='"+args.proxy+"'"


for port_info in args.ports.split('+'):

	dir_trozos = port_info.split('#')

	if len(dir_trozos) == 3:
		interfaz_local = dir_trozos[0].strip()
		interfaz_remota = dir_trozos[1].strip()
		los_puertos = dir_trozos[2].strip()
	elif len(dir_trozos) == 2:
		interfaz_remota = dir_trozos[0].strip()
		interfaz_local = 'localhost'
		los_puertos = dir_trozos[1].strip()
	else:
		interfaz_remota = 'localhost'
		interfaz_local = 'localhost'
		los_puertos = dir_trozos[0].strip()

	for puertos in los_puertos.split(','):

		puertos = puertos.strip().split('->')

		if len(puertos) == 1:

			rango = puertos[0].split(':')

			if len(rango) > 1:
				tot_open_files = tot_open_files + int(rango[1]) - int(rango[0]) + 1

				if max_open_files is not None and tot_open_files > max_open_files:
					cprint("ERROR: 'ulimit -n' is ["+str(max_open_files)+"]. REDUCE THE PORT RANGE or INCREASE THE VALUE OF 'ulimit -n'", "red", attrs=["bold"])
					sys.exit(1)

				for p in range(int(rango[0]), int(rango[1])+1):
					ssh_command_line = ssh_command_line + " -L "+interfaz_local+":"+str(p)+":"+interfaz_remota+":"+str(p)
			else:
				ssh_command_line = ssh_command_line + " -L "+interfaz_local+":"+str(puertos[0])+":"+interfaz_remota+":"+str(puertos[0])
		else:
			ssh_command_line = ssh_command_line + " -L "+interfaz_local+":"+str(puertos[0])+":"+interfaz_remota+":"+str(puertos[1])

	ssh_command_line = ssh_command_line + " " + args.destination

cprint(ssh_command_line, "cyan")

os.system(ssh_command_line)