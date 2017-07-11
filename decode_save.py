#!/usr/bin/python
#!coding=utf-8

import subprocess
import threading
import socket
import sqlite3
import struct
import Queue
import time
import sys
import re
import os

reload(sys)
sys.setdefaultencoding('utf8')


def covert_cellphone_num(num):
	phone_number = []
	for i in num:
		i = ord(i)
		i = (i << 4 & 0xF0) + (i >> 4 & 0x0F)
		phone_number.append(chr(i))
 
	return ("".join(phone_number).encode('hex'))[:-1]
 
def handle_message(**kargs):
	gsm_sms_segs = ""
 
	while True:
		data = kargs['messages'].get(True)
		if data[0:2] == '\x02\x04': #GSM_TAP header Version02 & HeaderLength 16bytes
 
			#uplink = struct.unpack('H', data[4:6])[0]
			#uplink = (uplink & 0x40 == 0x40)
			#print data.encode('hex')
			#skip header 16 bytes, directly handle the LAPDm part
			address_field = struct.unpack('B', data[16:17])[0]
			control_field = struct.unpack('B', data[17:18])[0]
			length_field =  struct.unpack('B', data[18:19])[0]
 
			if (address_field >> 2) & 0x1F == 3: # GSM SMS
				if (control_field & 0x01) == 0x00:  # frame type == information frame
					# caculate segments data length
					seg_len = (length_field >> 2) & 0x3F
					# if there are more segments
					has_segments = ((length_field >> 1) & 0x01 == 0x1)
					# caculate segments sequence
					seq = (control_field >> 1) & 0x07
 
					gsm_sms_segs += data[19:19+seg_len]
 
					# reassemble all segments when handling the last packet
					if has_segments == False:
 
						gsm_sms = gsm_sms_segs
						gsm_sms_segs = ""
 
						to_number = ""
						from_number = ""
						to_number_len = 0
						from_number_len = 0
						is_sms_submit = False
						is_sms_deliver = False
						has_tpudhi = False
						has_tpvpf = False
						is_mms = False
 
						if (len(gsm_sms) > 10 and ord(gsm_sms[0:1]) & 0x0F == 0x09) and (ord(gsm_sms[1:2]) == 0x01) and (ord(gsm_sms[2:3]) > 0x10): # SMS Message
							try:
								# print gsm_sms.encode('hex')
								# determinate if this is uplink message aka MS to Network
								is_uplink = (ord(gsm_sms[3:4]) == 0x00)
								print "***********************************************************************************************"
								print ("短信类型: 上行" if is_uplink else "短信类型: 下行")
 
								if is_uplink:
									to_number_len = struct.unpack('B', gsm_sms[6:7])[0] - 1
									to_number = gsm_sms[8:8+to_number_len]
									to_number = covert_cellphone_num(to_number)
 
									# check if this is SMS-SUBMIT
									sms_submit = struct.unpack('B', gsm_sms[7+to_number_len+2:7+to_number_len+2+1])[0]
									if sms_submit & 0x03 == 0x01:
										is_sms_submit = True
										# check if TP UD includes a extra header
										has_tpudhi = ((struct.unpack('B', gsm_sms[7+to_number_len+2:7+to_number_len+2+1])[0] & 0x40) == 0x40)
										has_tpvpf = ((struct.unpack('B', gsm_sms[7+to_number_len+2:7+to_number_len+2+1])[0] >> 3 & 0x02) == 0x02)
										from_number_len = struct.unpack('B', gsm_sms[8+to_number_len+3:8+to_number_len+3+1])[0]
										from_number_len = (from_number_len / 2) + (from_number_len % 2)
										from_number = gsm_sms[8+to_number_len+3+2:8+to_number_len+3+2+from_number_len]
										from_number = covert_cellphone_num(from_number)

										print "手机号码: %s" % from_number
										print "中心号码: %s" % to_number
										print "接收时间: %s" % GetCurrentTime()
		 
								else:
									to_number_len = struct.unpack('B', gsm_sms[5:6])[0] - 1
									to_number = gsm_sms[7:7+to_number_len]
									to_number = covert_cellphone_num(to_number)
 
									# check if this is SMS-DELIVER
									sms_deliver = struct.unpack('B', gsm_sms[7+to_number_len+2:7+to_number_len+2+1])[0]
									if sms_deliver & 0x03 == 0x0:
										is_sms_deliver = True
										# check if TP UD includes a extra header
										has_tpudhi = ((struct.unpack('B', gsm_sms[7+to_number_len+2:7+to_number_len+2+1])[0] & 0x40) == 0x40)
 
										from_number_len = struct.unpack('B', gsm_sms[7+to_number_len+3:7+to_number_len+3+1])[0]
										from_number_len = (from_number_len / 2) + (from_number_len % 2)
										from_number = gsm_sms[7+to_number_len+3+2:7+to_number_len+3+2+from_number_len]
										from_number = covert_cellphone_num(from_number)
 
										print "手机号码: %s" % from_number
										print "中心号码: %s" % to_number
										print "接收时间: %s" % GetCurrentTime()
 
								if is_sms_deliver:
									try:
										# if there is additional header, skip it
										header_len = 0
										if has_tpudhi:
											header_len = struct.unpack('B', gsm_sms[7+to_number_len+3+2+from_number_len+10:7+to_number_len+3+2+from_number_len+10+1])[0]
 
										mms = struct.unpack('B', gsm_sms[7+to_number_len+3+2+from_number_len+1:7+to_number_len+3+2+from_number_len+1+1])[0]
										if ((mms >> 2) & 0x03) == 0x01:
											is_mms = True
 
										if header_len == 0:
											sms = gsm_sms[7+to_number_len+3+2+from_number_len + 10:]
										else:
											sms = gsm_sms[7+to_number_len+3+2+from_number_len + 10 + header_len + 1:]

										if not is_mms:
											print '--------------------------------------'
											print sms.decode('UTF-16BE')
											print '--------------------------------------'
											saveToDB([from_number,to_number,is_uplink,sms.decode('UTF-16BE'),GetCurrentTime()])
										else:
											print '--------------------------------------'
											print "MMS 信息"
											print '--------------------------------------'
 
									except Exception as e:
										print '--------- Exception----------------'
										print e
										print '--------- Exception----------------'
 
								elif is_sms_submit:
									try:
										# if there is additional header, skip it
										header_len = 0
										# looks like uplink sms doesn't have a TP service centre time stamp
										if has_tpudhi:
											header_len = struct.unpack('B', gsm_sms[8+to_number_len+3+2+from_number_len+3:8+to_number_len+3+2+from_number_len+3+1])[0]
 
										mms = struct.unpack('B', gsm_sms[8+to_number_len+3+2+from_number_len+1:8+to_number_len+3+2+from_number_len+1+1])[0]
										if ((mms >> 2) & 0x03) == 0x01:
											is_mms = True
 
										if has_tpvpf:
											if header_len == 0:
												sms = gsm_sms[8+to_number_len+3+2+from_number_len + 3 + 1:]
											else:
												sms = gsm_sms[8+to_number_len+3+2+from_number_len + 3 + header_len + 1 + 1:]
										else:
											if header_len == 0:
												sms = gsm_sms[8+to_number_len+3+2+from_number_len + 3:]
											else:
												sms = gsm_sms[8+to_number_len+3+2+from_number_len + 3 + header_len + 1:]

										if not is_mms:
											print '--------------------------------------'
											print sms.decode('UTF-16BE')
											print '--------------------------------------'
											saveToDB([from_number,to_number,is_uplink,sms.decode('UTF-16BE'),GetCurrentTime()])
										else:
											print '--------------------------------------'
											print "MMS 信息"
											print '--------------------------------------'
									except Exception as e:
										print '--------- Exception----------------'
										print e
										print '--------- Exception----------------'
								else:
									print '--------------------------------------'
									print "短信状态报告"
									print '--------------------------------------'
							except Exception as e:
								print '--------- Exception----------------'
								print e
								print '--------- Exception----------------'

def GetCurrentTime():
	return time.strftime('%Y/%m/%d %H:%M:%S',time.localtime(time.time()))

def saveToDB(posData):
	try:
		cx = sqlite3.connect(sys.path[0]+"/smslog.db")
		cx.text_factory = str
		cu = cx.cursor()

		phone = posData[0]
		center = posData[1]
		smstype = unicode(posData[2])
		content = unicode(posData[3])
		date = posData[4]

		cu.execute("insert into sms (phone,center,type,content,date) values (?,?,?,?,?)", (phone,center,smstype,content,date))
		cx.commit()
		print '[√] Insert successly!'
		cu.close()
		cx.close()
	except Exception, e:
		print e

if __name__ == '__main__':
	try:
		que = Queue.Queue()
		thd = threading.Thread(target = handle_message, name = "handle_message_thread", kwargs = {'messages':que})
		thd.daemon = True
		thd.start()
		skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		skt.bind(('127.0.0.1', 4729))
		print "GSM sniffer is working !!! Enjoy it."
		while True:
			data, addr = skt.recvfrom(2048)
			# print data.encode('hex')
			que.put(data)
		skt.close()
	except Exception,e:
		print e