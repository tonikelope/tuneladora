#!/usr/bin/env python

import argparse
import os
import signal
import subprocess
import shlex
import sys
import re
from pyfiglet import figlet_format
from termcolor import cprint, colored
import time

VERSION = "1.16"

SSH_PROCESS = None

EXIT = False

def handler(signum, frame):
	global EXIT, SSH_PROCESS

	EXIT = True

	if SSH_PROCESS:
		cprint("EXTERNAL SIGTERM!", "red", attrs=["bold"])
		SSH_PROCESS.send_signal(signum)

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

			reverse = False

			if port3[0].lower() == 'r':
				reverse = True
				port3 = port3[1:]

			if port3.find(':') != -1:
				ports_split4 = [i.strip() for i in port3.split(':')]
				if 0 <= int(ports_split4[0]) <= 65535 and 0 <= int(ports_split4[1]) <= 65535 and int(ports_split4[0]) <= int(ports_split4[1]):
					ports_append['ports'].append({'pinit': ports_split4[0], 'pend': ports_split4[1], 'reverse':reverse})
				else:
					raise Exception('Bad port value/s or range!')
			elif port3.find('->') != -1:
				ports_split4 = [i.strip() for i in port3.split('->')]
				if 0 <= int(ports_split4[0]) <= 65535 and 0 <= int(ports_split4[1]) <= 65535:
					ports_append['ports'].append({'lport': ports_split4[1 if reverse else 0], 'rport': ports_split4[0 if reverse else 1], 'reverse':reverse})
				else:
					raise Exception('Bad port value/s!')
			elif 0 <= int(port3) <= 65535:
				ports_append['ports'].append({'lport': port3, 'rport': port3, 'reverse': reverse})
			else:
				raise Exception('Bad port value!')

		ports.append(ports_append)

	return ports

signal.signal(signal.SIGTERM, handler)

cprint(figlet_format("Tuneladora SSH"), "green", attrs=["bold"])

cprint("Tuneladora SSH "+VERSION+"\nA SSH port redirector for lazy people (made with love by tonikelope).", attrs=["bold"])

cprint("https://github.com/tonikelope/tuneladora\n")

parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=
	colored("Some examples:\n\n#1")+colored(" tuneladora 8080 bob@192.168.1.5", "green")+colored(" Redirects local port 8080 to remote port 8080 on remote machine 192.168.1.5 (remote user 'bob')")+colored("\n\n#2")+colored(" tuneladora '8080->80' alice@192.168.1.5", "green")+colored(" Redirects local port 8080 to remote port 80 on remote machine 192.168.1.5 (remote user 'alice')")+colored("\n\n#3")+colored(" tuneladora '8080->80+8081->81' 192.168.1.5", "green")+colored(" Redirects local port 8080 to remote port 80 and local port 8081 to remote port 81 on remote machine 192.168.1.5 (remote user same as local user)")+colored("\n\n#4")+colored(" tuneladora '8080:8085' 192.168.1.5", "green")+colored(" Same as '8080->8080+8081->8081+8082->8082+8083->8083+8084->8084+8085->8085' 192.168.1.5")+colored("\n\n#5")+colored(" tuneladora 'r8080->80' alice@192.168.1.5", "green")+colored(" (REVERSE) Redirects remote port 8080 to local port 80 on remote machine 192.168.1.5 (remote user 'alice')")+colored("\n\n#6")+colored(" tuneladora '172.26.0.15#localhost#8080' bob@192.168.1.5", "green")+colored(" Redirects local port 8080 of (local interface) 172.26.0.15 to remote port 8080 on remote machine 192.168.1.5 (remote user 'bob')")+colored("\n\n#7")+colored(" tuneladora '172.26.0.15#localhost#8080,9090+192.168.1.5#r9000->9100+10000:10005' bob@192.168.1.5", "green")+colored(" Redirects [local ports 8080 and 9090 of (local interface) 172.26.0.15 to remote ports 8080 and 9090 AND (REVERSE) redirects remote port 9000 to local port 9100 of (remote interface) 192.168.1.5 AND redirects local ports 10000 to 10005 to remote ports 10000 to 10005] ON remote machine 192.168.1.5 (remote user 'bob')"))

parser.add_argument("ports", help="[[local_address#]remote_address#][r]lport[->rport]|[r]port_init:port_end[,[r]lport[->rport]|[r]port_init:port_end[,...]][+[[local_address#]remote_address#][r]lport[->rport]|[r]port_init:port_end[,[r]lport[->rport]|[r]port_init:port_end[,...]][+...]]")

parser.add_argument("destination", help="[user@]host")

parser.add_argument('-p', '--sshport', default=None, help="Remote ssh port option")

parser.add_argument('-P', '--proxy', default=None, help="ssh ProxyCommand option")

parser.add_argument('-v', '--verbose', action='store_true', help="ssh verbose option")

args = parser.parse_args()

try:
	parsed_ports = parse_ports(args.ports)

	try:
		max_open_files = int(subprocess.check_output(["ulimit -n"], shell=True).decode())
	except:
		max_open_files = None

	tot_open_files = 0

	ssh_command_line = "ssh -N -o ServerAliveInterval=120 -o ServerAliveCountMax=2"

	if args.verbose:
		ssh_command_line=ssh_command_line+" -v"

	if args.sshport:
		ssh_command_line=ssh_command_line+" -p "+args.sshport

	if args.proxy:
		ssh_command_line=ssh_command_line+" -o ProxyCommand='"+args.proxy+"'"

	tot_open_files = 0

	for port_info in parsed_ports:

		for puertos in port_info['ports']:

			if 'lport' in puertos:
				if puertos['reverse']:
					ssh_command_line = ssh_command_line + " -R " + port_info['raddress'] + ":" + puertos['rport'] + ":" + port_info['laddress'] + ":" + puertos['lport']
				else:
					ssh_command_line = ssh_command_line + " -L " + port_info['laddress'] + ":" + puertos['lport'] + ":" + port_info['raddress'] + ":" + puertos['rport']
				tot_open_files = tot_open_files + 1
			else:
				for p in range(int(puertos['pinit']), int(puertos['pend']) + 1):
					if puertos['reverse']:
						ssh_command_line = ssh_command_line + " -R " + port_info['raddress'] + ":" + str(p) + ":" + port_info['laddress'] + ":" + str(p) 
					else:
						ssh_command_line = ssh_command_line + " -L " + port_info['laddress'] + ":" + str(p) + ":" + port_info['raddress'] + ":" + str(p)

				tot_open_files = tot_open_files + int(puertos['pend']) + 1 - int(puertos['pinit'])

	if max_open_files is not None and tot_open_files > max_open_files:
		cprint("ERROR: 'ulimit -n' is ["+str(max_open_files)+"]. REDUCE PORTS or INCREASE THE VALUE OF 'ulimit -n'", "red", attrs=["bold"])
	else:
		ssh_command_line = ssh_command_line + " " + args.destination
		
		while not EXIT:
			if args.verbose:
				cprint(ssh_command_line, "cyan")

			cprint("\nTunnel created and running...\n", "green", attrs=["bold"])

			try:
				SSH_PROCESS = subprocess.Popen(shlex.split(ssh_command_line))
				SSH_PROCESS.wait()
			except:
				pass

			if not EXIT:
				try:
					cprint('Tunnel closed. Opening again in 5 seconds... (CTRL + C to abort)', 'yellow')
					time.sleep(5)
				except KeyboardInterrupt:
					cprint('Auto-open aborted!', 'yellow')
					break

except Exception as e:
	cprint("ERROR: "+ str(e), "red", attrs=["bold"])
