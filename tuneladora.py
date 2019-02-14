#!/usr/bin/env python

import argparse
import os
import subprocess
import sys
import re
from pyfiglet import figlet_format
from termcolor import cprint, colored


def parse_ports(args_ports):
	m = re.findall('(?:(?:(?P<laddress>[^+#,]+) *?# *?)?(?P<raddress>[^+#,]+) *?# *?)?(?P<ports>(?:[0-9]+(?: *?(?:->|\:) *?[0-9]+)?(?: *?, *?(?:[0-9]+(?: *?(?:->|\:) *?[0-9]+))?)?)+)', args_ports)

	ports = []

	for port in m:
		p = {'local_address': port[0] if port[0] else 'localhost', 'remote_address': port[1] if port[1] else 'localhost', 'ports': []}

		m2 = re.findall('([0-9]+)(?: *?(->|\:) *?([0-9]+))?', port[2])

		for p2 in m2:
			if not p2[1] or p2[1] == '->':
				p['ports'].append({'lport': p2[0], 'rport':p2[2] if p2[2] else p2[0]})
			elif int(p2[0]) <= int(p2[2]):
				p['ports'].append({'port_init': p2[0], 'port_end':p2[2]})

		ports.append(p)

	return ports


cprint(figlet_format("Tuneladora SSH"), "green", attrs=["bold"])

cprint("Tuneladora SSH 1.1\nA SSH port redirector for lazy people (made with love by tonikelope).", attrs=["bold"])

parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=colored("Some examples:\n\n#1")+colored(" tuneladora 'localhost#localhost#8080' user@192.168.1.5", "green")+colored(" Redirects local port 8080 of (local) localhost to remote port 8080 of (remote) localhost on remote machine 192.168.1.5")+colored("\n\n#2")+colored(" tuneladora 8080 user@192.168.1.5", "green")+colored(" Same as #1 (default local/remote address is 'localhost')")+colored("\n\n#3")+colored(" tuneladora '8080:8081' user@192.168.1.5", "green")+colored(" Redirects local ports 8080 to 8081 of (local) localhost to remote ports 8080 to 8081 of (remote) localhost on remote machine 192.168.1.5")+colored("\n\n#4")+colored(" tuneladora '9000->10000' user@192.168.1.5", "green")+colored(" Redirects local port 9000 of (local) localhost to remote port 10000 of (remote) localhost on remote machine 192.168.1.5")+colored("\n\n#5")+colored(" tuneladora '192.168.100.3#localhost#8080,9090+192.168.1.5#9000->9100+10000:10005' user@192.168.1.5", "green")+colored(" Redirects local ports 8080 and 9090 of (local) 192.168.100.3 to remote ports 8080 and 9090 of (remote) localhost AND redirects local port 9000 of (local) localhost to remote port 9100 of (remote) 192.168.1.5 AND redirects local ports 10000 to 10005 of (local) localhost to remote ports 10000 to 10005 of (remote) localhost ON remote machine 192.168.1.5"))

parser.add_argument("ports", help="[[local_address#]remote_address#]<lport[->rport]|port_init:port_end[,lport[->rport]|port_init:port_end[,...]]>[+[[local_address#]remote_address#]<lport[->rport]|port_init:port_end[,lport[->rport]|port_init:port_end[,...]]>[+...]]")

parser.add_argument("destination", help="Destination host.")

parser.add_argument('--proxy', help="ssh -o ProxyCommand='THIS STUFF'")

args = parser.parse_args()

ssh_command_line = "ssh -N"

try:
	max_open_files = int(subprocess.check_output(["ulimit -n"], shell=True).decode())
except:
	max_open_files = None

tot_open_files = 0

if args.proxy:
	ssh_command_line=ssh_command_line+" -o ProxyCommand='"+args.proxy+"'"

parsed_ports = parse_ports(args.ports)

tot_open_files = 0

if len(parsed_ports) > 0:

	for port_info in parsed_ports:

		for puertos in port_info['ports']:

			if 'lport' in puertos:
				ssh_command_line = ssh_command_line + " -L "+port_info['local_address']+":"+puertos['lport']+":"+port_info['remote_address']+":"+puertos['rport']
				tot_open_files = tot_open_files + 1
			else:
				for p in range(int(puertos['port_init']), int(puertos['port_end'])+1):
					ssh_command_line = ssh_command_line + " -L "+port_info['local_address']+":"+str(p)+":"+port_info['remote_address']+":"+str(p)

				tot_open_files = tot_open_files + int(puertos['port_end']) + 1 - int(puertos['port_init'])

	ssh_command_line = ssh_command_line + " " + args.destination

	cprint(ssh_command_line, "cyan")

	if max_open_files is not None and tot_open_files > max_open_files:
		cprint("ERROR: 'ulimit -n' is ["+str(max_open_files)+"]. REDUCE PORTS or INCREASE THE VALUE OF 'ulimit -n'", "red", attrs=["bold"])
		sys.exit(1)

	os.system(ssh_command_line)
else:
	cprint("ERROR: nothing to do", "red", attrs=["bold"])