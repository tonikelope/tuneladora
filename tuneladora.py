#!/usr/bin/env python

import argparse
import os
import subprocess
import sys
import re
from pyfiglet import figlet_format
from termcolor import cprint, colored
import time

VERSION = "1.11"

def parse_ports(args_ports):
	ports = []

	ports_split1 = [i.strip() for i in args_ports.split('+')]

	for port1 in ports_split1:

		ports_split2 = [i.strip() for i in port1.split('#')]

		l = len(ports_split2)

		ports_append = {'laddress': ports_split2[l-3] if l==3 else 'localhost', 'raddress': ports_split2[l-2] if l >= 2 else 'localhost', 'ports': []}
		
		ports_info = ports_split2[l-1]

		ports_split3 = [i.strip() for i in ports_info.split(',')]

		for port3 in ports_split3:
			if port3.find(':') != -1:
				ports_split4 = [i.strip() for i in port3.split(':')]
				if 0 <= int(ports_split4[0]) <= 65535 and 0 <= int(ports_split4[1]) <= 65535 and int(ports_split4[0]) <= int(ports_split4[1]):
					ports_append['ports'].append({'pinit': ports_split4[0], 'pend': ports_split4[1]})
				else:
					raise Exception('Bad port value/s or range!')
			elif port3.find('->') != -1:
				ports_split4 = [i.strip() for i in port3.split('->')]
				if 0 <= int(ports_split4[0]) <= 65535 and 0 <= int(ports_split4[1]) <= 65535:
					ports_append['ports'].append({'lport': ports_split4[0], 'rport': ports_split4[1]})
				else:
					raise Exception('Bad port value/s!')
			elif 0 <= int(port3) <= 65535:
				ports_append['ports'].append({'lport': port3, 'rport': port3})
			else:
				raise Exception('Bad port value!')

		ports.append(ports_append)

	return ports

cprint(figlet_format("Tuneladora SSH"), "green", attrs=["bold"])

cprint("Tuneladora SSH "+VERSION+"\nA SSH port redirector for lazy people (made with love by tonikelope).", attrs=["bold"])

cprint("https://github.com/tonikelope/tuneladora\n")

parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=colored("Some examples:\n\n#1")+colored(" tuneladora 'localhost#localhost#8080' user@192.168.1.5", "green")+colored(" Redirects local port 8080 of (local) localhost to remote port 8080 of (remote) localhost on remote machine 192.168.1.5")+colored("\n\n#2")+colored(" tuneladora 8080 user@192.168.1.5", "green")+colored(" Same as #1 (default local/remote address is 'localhost')")+colored("\n\n#3")+colored(" tuneladora '8080:8081' user@192.168.1.5", "green")+colored(" Redirects local ports 8080 to 8081 of (local) localhost to remote ports 8080 to 8081 of (remote) localhost on remote machine 192.168.1.5")+colored("\n\n#4")+colored(" tuneladora '9000->10000' user@192.168.1.5", "green")+colored(" Redirects local port 9000 of (local) localhost to remote port 10000 of (remote) localhost on remote machine 192.168.1.5")+colored("\n\n#5")+colored(" tuneladora '192.168.100.3#localhost#8080,9090+192.168.1.5#9000->9100+10000:10005' user@192.168.1.5", "green")+colored(" Redirects local ports 8080 and 9090 of (local) 192.168.100.3 to remote ports 8080 and 9090 of (remote) localhost AND redirects local port 9000 of (local) localhost to remote port 9100 of (remote) 192.168.1.5 AND redirects local ports 10000 to 10005 of (local) localhost to remote ports 10000 to 10005 of (remote) localhost ON remote machine 192.168.1.5"))

parser.add_argument("ports", help="[[local_address#]remote_address#]lport[->rport]|port_init:port_end[,lport[->rport]|port_init:port_end[,...]][+[[local_address#]remote_address#]lport[->rport]|port_init:port_end[,lport[->rport]|port_init:port_end[,...]][+...]]")

parser.add_argument("destination", help="[user@]host")

parser.add_argument('-r', '--reverse', action='store_true', help="Reverse tunnel")

parser.add_argument('-p', '--proxy', default=None, help="ssh ProxyCommand option")

args = parser.parse_args()

try:
	parsed_ports = parse_ports(args.ports)

	try:
		max_open_files = int(subprocess.check_output(["ulimit -n"], shell=True).decode())
	except:
		max_open_files = None

	tot_open_files = 0

	ssh_command_line = "ssh -N"

	if args.proxy:
		ssh_command_line=ssh_command_line+" -o ProxyCommand='"+args.proxy+"'"

	tot_open_files = 0

	for port_info in parsed_ports:

		for puertos in port_info['ports']:

			if 'lport' in puertos:
				if args.reverse:
					puerto_remoto = puertos['rport']
					puertos['rport'] = puertos['lport']
					puertos['lport'] = puerto_remoto
					ssh_command_line = ssh_command_line + " -R " + port_info['raddress'] + ":" + puertos['rport'] + ":" + port_info['laddress'] + ":" + puertos['lport']
				else:
					ssh_command_line = ssh_command_line + " -L " + port_info['laddress'] + ":" + puertos['lport'] + ":" + port_info['raddress'] + ":" + puertos['rport']
				tot_open_files = tot_open_files + 1
			else:
				for p in range(int(puertos['pinit']), int(puertos['pend']) + 1):
					if args.reverse:
						ssh_command_line = ssh_command_line + " -R " + port_info['raddress'] + ":" + str(p) + ":" + port_info['laddress'] + ":" + str(p) 
					else:
						ssh_command_line = ssh_command_line + " -L " + port_info['laddress'] + ":" + str(p) + ":" + port_info['raddress'] + ":" + str(p)

				tot_open_files = tot_open_files + int(puertos['pend']) + 1 - int(puertos['pinit'])

	if max_open_files is not None and tot_open_files > max_open_files:
		cprint("ERROR: 'ulimit -n' is ["+str(max_open_files)+"]. REDUCE PORTS or INCREASE THE VALUE OF 'ulimit -n'", "red", attrs=["bold"])
	else:
		ssh_command_line = ssh_command_line + " " + args.destination
		
		while True:
			cprint(ssh_command_line, "cyan")

			os.system(ssh_command_line)

			try:
				cprint('Tunnel closed. Opening again in 5 seconds... (CTRL + C to abort)', 'yellow')
				time.sleep(5)
			except KeyboardInterrupt:
				cprint('Aborted!', 'yellow')
				break


except Exception as e:
	cprint("ERROR: "+ str(e), "red", attrs=["bold"])
