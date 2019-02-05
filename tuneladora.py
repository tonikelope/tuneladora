#!/usr/bin/env python

import argparse
import os
from pyfiglet import figlet_format
from termcolor import cprint
import subprocess
import sys

cprint(figlet_format("Tuneladora SSH"), "green", attrs=["bold"])

print("Tuneladora SSH 0.3\nA SSH port redirector for lazy people (made with love by tonikelope).\n")

parser = argparse.ArgumentParser()

parser.add_argument("destination", help="Destination host.")

parser.add_argument("ports", help="[local_address#]remote_address#local_port[->remote_port]. Example: localhost#localhost#8080 (this redirects port 8080 of the localhost interface to port 8080 of the localhost interface on the destination host).")

parser.add_argument('-o', help='SSH proxy command')

args = parser.parse_args()

ssh_command_line = "ssh -N"

try:
	max_open_files = int(subprocess.check_output(["ulimit -n"], shell=True).decode())
except:
	max_open_files = None

tot_open_files = 0

if args.o:
	ssh_command_line=ssh_command_line+" -o ProxyCommand='"+args.o+"'"

for port_dir in args.ports.split('|'):
	
	dir_trozos = port_dir.split('#')

	if len(dir_trozos) == 3:
		interfaz_local = dir_trozos[0].strip()
		interfaz_remota = dir_trozos[1].strip()
		los_puertos = dir_trozos[2].strip()
	else:
		interfaz_remota = dir_trozos[0].strip()
		interfaz_local = 'localhost'
		los_puertos = dir_trozos[1].strip()

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