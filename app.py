#!/usr/bin/env python
#!coding=utf-8
# author 92ez.com

import webbrowser
import subprocess
import sqlite3
import serial
import time
import json
import sys
import web
import re
import os

reload(sys)
sys.setdefaultencoding('utf8')

urls = (
	"/","index",
	"/getList","getList",
	"/killdev","killDev",
	"/getUSB","getUSB",
	"/getSMS","getSMS",
	"/resetPower","resetPower",
	"/downloadAll","downloadAll",
	"/download","download",
	"/readARFCN","readARFCN",
	"/getARFCN","getARFCN",
	"/doSniffer","doSniffer"
)

#static 
render = web.template.render('static',cache = False)

#init program
class index:
	def GET(self):
		subprocess.Popen("rm -rf *.dat",shell = True)
		return render.index("static")

class killDev:
	def POST(self):
		subprocess.Popen("killall ccch_scan cell_log osmocon 2>/dev/null",shell = True)
		for i in range(1, 9):
			os.system('> /home/unicorn/smsweb-master/arfcn_%s.log' % i)
		return json.dumps({"res":0}) 

class resetPower:
	def POST(self):
		sw = serial.Serial(USBLIST[0],115200)
		#powerPort = range(2,10)
		#for port in powerPort:
		try:
				print '[*] Turn off all c118'#+str(port)
				sw.write('\xFF\xFF\x04\x01\x00\x00\xA5')
				#time.sleep(4)
		except Exception,e:
				return json.dumps({"res":-1,"msg":str(e)})
		return json.dumps({"res":0})

class getUSB:
	def POST(self):
		global USBLIST
		USBLIST = []

		subPro2 = subprocess.Popen('ls /dev | grep ttyUSB', shell=True,stdout = subprocess.PIPE)
		subPro2.wait()
		ttylog = subPro2.communicate()

		ttyusbList = ttylog[0].split('\n')

		del ttyusbList[len(ttyusbList)-1]

		for u in range(len(ttyusbList)):
			USBLIST.append('/dev/'+ttyusbList[u])

		return json.dumps({"total":len(USBLIST),"rows":USBLIST})

class downloadAll:
	def POST(self):
		sw = serial.Serial(USBLIST[0],115200)
		#keyPort = ['10','11','12','14','15','16','17','19']

		del USBLIST[0]

		for dev in USBLIST:
			try:
				downloadCommand = ['xterm',"-T","osmocon for "+dev,'-e',sys.path[0]+'/osmocombb_x64/osmocon','-m','c123xor','-s','/tmp/osmocom_l2_'+ dev.split('USB')[1] ,'-p',dev,sys.path[0]+'/osmocombb_x64/layer1.compalram.bin']
				downloadProcess = subprocess.Popen(downloadCommand,stderr=subprocess.PIPE,stdout=subprocess.PIPE)
				time.sleep(0.5)
			except Exception,e:
				return json.dumps({"res":-1,"msg":str(e)})

		#for port in keyPort:
		try:
				sw.write('\xFF\xFF\x04\x01\x3F\x3F\x22')
				time.sleep(8)
		except Exception,e:
				return json.dumps({"res":-1,"msg":str(e)})
		#time.sleep(4)
		return json.dumps({"res":0})

class download:
	def POST(self):
		deviceId = str(web.input().get('devid'))
		sw = serial.Serial(USBLIST[0],115200)
		keyPort = ['10','11','12','14','15','16','17','19']

		try:
			downloadCommand = ['xterm',"-T","osmocon for "+deviceId,'-e',sys.path[0]+'/osmocombb_x64/osmocon','-m','c123xor','-s','/tmp/osmocom_l2_'+ deviceId.split('USB')[1] ,'-p',deviceId,sys.path[0]+'/osmocombb_x64/layer1.compalram.bin']
			downloadProcess = subprocess.Popen(downloadCommand,stderr=subprocess.PIPE,stdout=subprocess.PIPE)
			time.sleep(1)
		except Exception,e:
			return json.dumps({"res":-1,"msg":str(e)})

		#for port in keyPort:
		try:
				sw.write('\xFF\xFF\x04\x01\x3F\x3F\x22')
				time.sleep(0.5)
		except Exception,e:
				return json.dumps({"res":-1,"msg":str(e)})
		#time.sleep(4)
		return json.dumps({"res":0})

class readARFCN:
	def POST(self):
		deviceId = str(web.input().get('devid'))
		arfcnlist = []
		try:
			for line in open(sys.path[0]+"/arfcn_"+deviceId+".log"): 
				arfcnlist.append(line.replace('\r\n',''))
		except Exception,e:
			return json.dumps({"res":-1,"msg":str(e)})
		return json.dumps({"res":0,"rows":arfcnlist[:-1],"date":arfcnlist[-1]})

class getARFCN:
	def POST(self):
		deviceId = str(web.input().get('devid'))
		try:
			devIndex = deviceId.split('USB')[1]
			cellLogshell = [sys.path[0]+"/osmocombb_x64/cell_log","-s","/tmp/osmocom_l2_"+ devIndex,"-O"];
			arfcnScan = subprocess.Popen(cellLogshell,stderr=subprocess.PIPE,stdout=subprocess.PIPE)
			scanlog = arfcnScan.communicate()
			arfcnScan.wait()
			scanloginfo = ";".join(scanlog)
			scanbase = re.findall(r"ARFCN\=[^)]+\)",scanloginfo)

			logfile = file(sys.path[0]+"/arfcn_"+ devIndex +".log","w+")
			for line in scanbase:
				logfile.write(str(line)+"\r\n")
			logfile.write('Date: '+GetCurrentTime())
			logfile.close()
		except Exception,e:
			return json.dumps({"res":-1,"msg":str(e)})
		return json.dumps({"res":0,"rows":scanbase,"date":GetCurrentTime()})

class doSniffer:
	def POST(self):
		try:
			arfcnId = str(web.input().get('arfcn'))
			devindex = str(web.input().get('devid')).split('USB')[1]
			sniffcommand = ["xterm","-T","Sniffer for "+web.input().get('devid'),"-e",sys.path[0]+"/osmocombb_x64/ccch_scan","-s","/tmp/osmocom_l2_"+devindex,"-i","127.0.0.1","-a",arfcnId]
			snifferProcess =  subprocess.Popen(sniffcommand,stderr=subprocess.PIPE,stdout=subprocess.PIPE)
		except Exception,e:
			return json.dumps({"res":-1,"msg":str(e)})
		return json.dumps({"res":0,"pid":snifferProcess.pid})

class getList:
	def GET(self):
		return render.list("static")

class getSMS:
	def POST(self):
		page = int(web.input().get("page"))
		rows = int(web.input().get("rows"))
		limitCount = (page-1)*rows

		try:
			cx = sqlite3.connect(sys.path[0]+"/smslog.db")
			cu = cx.cursor()
			queryCount = cu.execute("SELECT count(id) FROM sms")
			queryLength = queryCount.fetchone()[0]
			cu.close()
			cx.close()
		except Exception, e:
			print e

		SMSStr =[]

		try:
			cx = sqlite3.connect(sys.path[0]+"/smslog.db")
			cx.text_factory = str
			cu = cx.cursor()

			queryList = cu.execute("SELECT * FROM sms order by date desc limit %d,%d" % (limitCount,rows))

			for row in queryList.fetchall():
				this_id = row[0]
				this_phone = row[1]
				this_center = row[2]
				this_type = row[3]
				this_content = row[4]
				this_date = row[5]

				SMSStr.append({"id":this_id,"phone": this_phone, "center": this_center, "type": this_type,"content": this_content, "date": this_date})
			
			cu.close()
			cx.close()
		except Exception,e:
			return json.dumps({"res":-1,"msg":str(e)})
			
		return json.dumps({"res":0,"rows":SMSStr,"total":queryLength})

def GetCurrentTime():
	return time.strftime('%Y/%m/%d %H:%M:%S',time.localtime(time.time()))

if __name__ == "__main__":
	sniffcommand = ["xterm","-T","Decode and save","-e",'python',sys.path[0]+"/decode_save.py"]
	snifferProcess =  subprocess.Popen(sniffcommand,stderr=subprocess.PIPE,stdout=subprocess.PIPE)
	webbrowser.open("http://localhost:"+sys.argv[1], new=0, autoraise=True)
	app = web.application(urls,globals())
	app.run()
