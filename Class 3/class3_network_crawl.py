from cdp_parse import *
import os
import netmiko
import re
from getpass import getpass


#This is a way to try and make the connections with SSH, if that fails we try telnet, if that fails also it puts an entry in
#Issues.csv and returns a None
def make_connection (ip,username,password):
	try:
		return netmiko.ConnectHandler(device_type='cisco_ios', ip=ip, username=username, password=password)
	except:
		try:
			return netmiko.ConnectHandler(device_type='cisco_ios_telnet', ip=ip, username=username, password=password)
		except:
			issue = ip+ ", can't be ssh/telneted to"
			to_doc_a("Issues.csv", issue)
			to_doc_a("Issues.csv", '\n')
			return None

#These functions are covered in part 1 http://packetpushers.net/intro-python-network-automation/
def to_doc_a(file_name, varable):
	f=open(file_name, 'a')
	f.write(varable)
	f.close()	
def to_doc_w(file_name, varable):
	f=open(file_name, 'w')
	f.write(varable)
	f.close()


#This function is covered in part 1 http://packetpushers.net/intro-python-network-automation/
def get_ip (input):
	return(re.findall(r'(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?).){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)', input))

#This function is a modified version of what we covered in part 1 http://packetpushers.net/intro-python-network-automation/
#This time it doesn't mess with variables outside of the function which makes it MUCH easier to keep track of what's going on
#inside your program, and also makes the code more reusable in the future.
def get_ips (file_name):
	ips = []
	for line in open(file_name, 'r').readlines():
		line = get_ip(line)
		for ip in line: 
			ips.append(ip)
	return ips
			
#A document with where to start the CDP crawl in the network
seed_data_file = "seed_ips.txt"

#This one will be the devices we have already done, that way we should avoid going around in a circle.
already_done = []

#Import the starter IPs
to_do = get_ips (seed_data_file)

#Prompt user for account info
username = input("Username: ")
password = getpass()

#start going though the devices one by one
for device in to_do:
	#I at least like some output to see what my program is doing.
	#print (device)
	#Make sure it's not something we have already done, if we don't we'll just end up going in circles at some point
	if device in already_done:
		print (device + " is already done")
		#continue skips this round of the for loop and moves on to the next one.
		continue
	
	net_connect = make_connection (device,username,password)
	if net_connect == None:
		continue
	
	#This will print out the prompt you have up, in Cisco that is the hostname and the actual prompt normally # or >, 
	#we don't want either so we remove the last character
	hostname = net_connect.find_prompt()[:-1]
	
	#Next lets find all the IPs on this device and add them to the already_done list so we don't come back to this device a 2ed time
	
	#Pull output from show ip int brief
	dev_ips =net_connect.send_command_expect('show ip int brief')
	
	#find all the IPs in that output
	dev_ips = get_ip (dev_ips)
	
	#Add those IPs to the done section
	for dev_ip in dev_ips:
		already_done.append (dev_ip)
	
	#Pull the CDP info and put it into a file
	cdp_info =net_connect.send_command_expect('show cdp entry *')
	cdp_filename = hostname + " cdp_info"
	to_doc_a(cdp_filename, cdp_info)
	
	#now for the crawl part, we use the CDP parsing we did back in lession 2 http://packetpushers.net/intro-python-network-automation-part-2/
	#and we feed it the  CDP info we just grabbed.
	parsed_cdp =  parse_cdp_out(cdp_filename)
	#and pull the IPs out of it, and tell the system to go do the same to those.
	for each_cdp_entry in parsed_cdp:
		#Sadly we have to put a try in here as some Cisco devices don't always give us an IP
		try:	
			to_do.append(each_cdp_entry['remote_ip'])
		except:
			print (each_cdp_entry['remote_id'] + " Didn't have an IP")
			pass
			
	
		
	



