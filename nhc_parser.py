# -*- coding: utf-8 -*-
import bs4
from bs4 import BeautifulSoup
import requests
import re
import datetime
from rangedict import RangeDict
import os
import json
from trpcl_adv_fpath import *


class ForecastValid:
	def __init__(self, lat, latd, lon, lond, ftime, mwind, mgust):
		self.lat  = lat.strip()
		self.latd = latd.strip()
		self.lon  = lon.strip()
		self.lond = lond.strip()
		self.ftime = ftime.strip()
		self.maxwind = mwind.strip()
		self.maxgusts = mgust.strip()

	def get_fv_text(self):
		return "Forecast %s %s%s/%s%s Max winds %s/%sKT. " % (self.ftime, self.lat, self.latd, self.lon, self.lond, self.maxwind, self.maxgusts)

class OutlookValid:
	def __init__(self, lat, latd, lon, lond, ftime, mwind, mgust):
		self.lat  = lat
		self.latd = latd
		self.lon  = lon
		self.lond = lond
		self.ftime = ftime
		self.maxwind = mwind
		self.maxgusts = mgust

	def get_ov_text(self):
		return "Outlook %s %s%s/%s%s Max winds %s/%sKT. " % (self.ftime, self.lat, self.latd, self.lon, self.lond, self.maxwind, self.maxgusts)		

class NHCParser:
	__wmo_nn_re = re.compile("(.*) FORECAST/ADVISORY NUMBER (.*)")
	__wmo_center_re = re.compile("(.*) CENTER LOCATED NEAR\s+(\d*\.\d*)(N|S)\s+(\d*\.\d*)(E|W) AT (.*)")
	__wmo_loc_acc_re = re.compile("POSITION ACCURATE WITHIN (.*) NM")
	__hr_st_re = re.compile("(?P<type>.*)?\s*(?P<kind>HURRICANE|CYCLONE|STORM|DEPRESSION|DISTURBANCE|TYPHOON|REMNANTS)\s*(?P<conjct>OF)?\s*(?P<name>.*)")	# POST-TROPICAL CYCLONE JOSE  	# TROPICAL STORM JOSE
	__tc_id_re = re.compile("\s*NWS\s*NATIONAL\s*HURRICANE\s*CENTER\s*MIAMI\s*FL\s*(?P<tc_id>.*)\s*")
	__wmo_mov_re = re.compile("PRESENT MOVEMENT TOWARD THE (.*) OR (.*) DEGREES AT (.*) KT")
	__max_swww_re = re.compile("MAX SUSTAINED WINDS (.*) KT WITH GUSTS TO (.*) KT.")
	__fvalid_re = re.compile("FORECAST VALID\s+(.*)\s+(\d*\.\d*)(N|S)\s+(\d*\.\d*)(E|W)([./]{3})?(.*)?")
	__ovalid_re = re.compile("OUTLOOK VALID\s+(.*)\s+(\d*\.\d*)(N|S)\s+(\d*\.\d*)(E|W)([./]{3})?(.*)?")	#OUTLOOK VALID 21/1200Z 54.0N 71.0W...EXTRATROPICAL
	__max_fo_re = re.compile("MAX WIND\s+(.*)\s+KT([./]{3})?GUSTS\s+(.*)\s+KT.")

	__dir_map = {(0.00, 11.25): 'N',(11.25, 33.75): 'NNE', (33.75, 56.25): 'NE',(56.25, 78.75): 'ENE', (78.75, 101.25): 'E',
		(101.25, 123.75): 'ESE', (123.75, 146.25): 'SE', (146.25, 168.75): 'SSE',  (168.75, 191.25): 'S',
		(191.25, 213.75): 'SSW', (213.75, 236.25): 'SW', (236.25, 258.75): 'WSW', (258.75, 281.25): 'W',
		(281.25, 303.75): 'WNW',(303.75, 326.25): 'NW',(326.25, 348.75): 'NNW', (348.75, 361.00): 'N'}

	__dirnotation = RangeDict(__dir_map)

	def __init__(self,**kwargs):
		self.tc_id = None
		self.wmo_header = [] 			# WMO Header
		self.wwn = ""					# Watches/Warnings and News
		self.storm_loc = []				# Storm Location
		self.storm_mov = []				# Storm Movement
		self.mcp = "" 					# Minimum Central Pressure
		self.ese= ""					# Eye Size Estimate
		self.maxswww = [] 				# Max Sustained Wind, Wind Radii, and 12-Foot Wave Height Radii Section Repeat
		self.fvalid_header = []
		self.ovalid_header = []
		self.ovalid = []
		self.fvalid = []
		self.fs_12hr = "" 				# 12-Hour Forecast
		self.fs_24hr = "" 				# 24-Hour Forecast
		self.fs_36hr = "" 				# 36-Hour Forecast
		self.fs_48hr = "" 				# 48-Hour Forecast
		self.fs_72hr = "" 				# 72-Hour Forecast
		self.fs_96hr = "" 				# 96-Hour Forecast
		self.fs_120hr = "" 				# 120-Hour Forecast
		self.fs_rsr = "" 				# Request for Ship Reports
		self.next_adv = "" 				# Next Advisory
		self.text_forecastf = None
		if 'filename' in kwargs:
			self.text_forecastf = kwargs['filename']	
			#print self.text_forecastf

	def set_headers():
		pass

	def parse_headers():
		pass

	def get_textforecastf(self):
		if self.text_forecastf:
			return self.text_forecastf
		return None

	def set_paras(self):
		if self.text_forecastf:
			with open(self.text_forecastf,'r') as far:
				lines = far.readlines()
				#self.wmo_header = [line.replace('\n', '') for line in lines[:7]]
				bline_count = 0
				lindex = 0

				for line in lines:
					wmo_header_m = self.__wmo_nn_re.match(line)
					if wmo_header_m is not None:
						#print wmo_header_m.groups()
						while lines[lindex].strip().replace('\n','') != '':
							self.wmo_header.append(lines[lindex].replace('\n',''))
							lindex = lindex + 1
						print self.wmo_header
						"""
						self.wmo_header.append(line.replace('\n',''))
						lindex = lindex + 1
						self.wmo_header.append(lines[lindex].replace('\n',''))
						lindex = lindex + 1
						self.wmo_header.append(lines[lindex].replace('\n',''))
						"""
						break
					lindex = lindex + 1

				idx = lindex
				for line in lines[lindex:]:
					wmo_c = self.__wmo_center_re.match(line)
					if wmo_c is not None:
						self.storm_loc.append(line.replace('\n', ''))
						self.storm_loc.append(lines[idx+1].replace('\n', ''))
						self.storm_mov.append(lines[idx+3].replace('\n', ''))

						break
					idx = idx + 1

				sindex = idx
				pindex = idx
				if idx>=len(lines):
					sindex = lindex
				else:
					sindex = idx
					pindex = idx

				for line in lines[sindex:]:
					maxswww_m = self.__max_swww_re.match(line)
					if maxswww_m:
						self.maxswww.append(line.replace('\n', '')) 
						break
					idx = idx + 1

				if idx>=len(lines):
					sindex = pindex
				else:
					sindex = idx
					pindex = idx

				for line in lines[sindex:]:
					fvalid_m = self.__fvalid_re.match(line)
					if fvalid_m:
						fvalidi = []
						fvalidi.append(lines[idx].strip())
						fvalidi.append(lines[idx+1].strip())
						self.fvalid_header.append(fvalidi)
						#print fvalidi		
					idx = idx + 1

				#print idx, len(lines), pindex
				#print lines[pindex]
				if idx>=len(lines):
					sindex = pindex
					idx = pindex
				else:
					sindex = idx
					pindex = idx

				for line in lines[sindex:]:
					ovalid_m = self.__ovalid_re.match(line)
					if ovalid_m:
						ovalidi = []
						ovalidi.append(line.strip())
						ovalidi.append(lines[idx+1].strip())
						self.ovalid_header.append(ovalidi)
						#print ovalidi						
					idx = idx + 1


			##print self.storm_loc

	def get_wmo_header(self):
		return self.wmo_header

	def parse_wmo_header_orig(self):
		if self.wmo_header:
			#print self.wmo_header[2]
			wmo_hs_name = self.__wmo_nn_re.match(self.wmo_header[2])
			#print wmo_hs_name.groups()
			if wmo_hs_name:
				hr_st = wmo_hs_name.groups()[0]				
				#print ht_st
				hs_type_name_m = self.__hr_st_re.match(hr_st)

				if len(hs_type_name_m.groups())==3 and hs_type_name_m.groups()[0] is not None:
					self.hr_st_type = hs_type_name_m.groups()[0].strip()
					self.cy_or_st = hs_type_name_m.groups()[1].strip()
					self.hr_st_name = hs_type_name_m.groups()[2].strip()
					self.hr_st_adv_num = wmo_hs_name.groups()[1].strip()
				if len(hs_type_name_m.groups())==3 and hs_type_name_m.groups()[0] is None:	
					self.hr_st_type = None
					self.cy_or_st = hs_type_name_m.groups()[1].strip()
					self.hr_st_name = hs_type_name_m.groups()[2].strip()
					self.hr_st_adv_num = wmo_hs_name.groups()[1].strip()

			ts = self.wmo_header[len(self.wmo_header)-1] #'2100 UTC FRI SEP 22 2017'
			tsf = '%H%M %Z %a %b %d %Y'
			dts = datetime.datetime.strptime(ts,tsf)
			self.wmo_issue_ts = dts
			#print self.hr_st_type, self.cy_or_st, self.hr_st_name, self.hr_st_adv_num, self.wmo_issue_ts			

	def parse_wmo_header(self):
		if self.wmo_header:
			#print self.wmo_header[0]
			wmo_hs_name = self.__wmo_nn_re.match(self.wmo_header[0])
			#print wmo_hs_name.groups()[0]
			if wmo_hs_name is not None:
				hr_st = wmo_hs_name.groups()[0]
				hs_type_name_m = self.__hr_st_re.match(hr_st)
				hs_data = hs_type_name_m.groupdict()
				self.hr_st_type = hs_data['type']	# hs_type_name_m.groups()[0].strip()
				self.cy_or_st = hs_data['kind'] 	# hs_type_name_m.groups()[1].strip()
				self.hr_st_name = hs_data['name']	# hs_type_name_m.groups()[2].strip()
				self.hr_st_adv_num = wmo_hs_name.groups()[1].strip()

				tc_id_raw = self.wmo_header[1]
				#print tc_id_raw
				tc_id_m = self.__tc_id_re.match(tc_id_raw)
				if tc_id_m:
					self.tc_id = tc_id_m.groupdict()['tc_id']

				"""
				if len(hs_type_name_m.groups())==3 and hs_type_name_m.groups()[0] is not None:
					self.hr_st_type = #hs_type_name_m.groups()[0].strip()
					self.cy_or_st = #hs_type_name_m.groups()[1].strip()
					self.hr_st_name = #hs_type_name_m.groups()[2].strip()
					self.hr_st_adv_num = wmo_hs_name.groups()[1].strip()
				if len(hs_type_name_m.groups())==3 and hs_type_name_m.groups()[0] is None:	
					self.hr_st_type = None
					self.cy_or_st = hs_type_name_m.groups()[1].strip()
					self.hr_st_name = hs_type_name_m.groups()[2].strip()
					self.hr_st_adv_num = wmo_hs_name.groups()[1].strip()
				"""
			ts = self.wmo_header[len(self.wmo_header)-1] #'2100 UTC FRI SEP 22 2017'
			tsf = '%H%M %Z %a %b %d %Y'
			dts = datetime.datetime.strptime(ts,tsf)
			self.wmo_issue_ts = dts
			#print self.hr_st_type, self.cy_or_st, self.hr_st_name, self.hr_st_adv_num, self.wmo_issue_ts			

	def parse_storm_loc_header(self):
		if self.storm_loc:
			loc_time_m = self.__wmo_center_re.match(self.storm_loc[0])
			#print loc_time_m.groups()
			if loc_time_m:
				self.lat, self.latd = loc_time_m.groups()[1].strip(), loc_time_m.groups()[2].strip()
 				self.lon, self.lond = loc_time_m.groups()[3].strip(), loc_time_m.groups()[4].strip()
				self.ctime = loc_time_m.groups()[5].strip()
				#print lat, latd, lon, lond, ctime	
			loc_acc_m = self.__wmo_loc_acc_re.match(self.storm_loc[1])
			if loc_acc_m:
				loc_acc = loc_acc_m.groups()[0].strip()
				#print loc_acc.strip()

	def parse_storm_mov_header(self):
		if self.storm_mov:
			wmo_dir_speed_m = self.__wmo_mov_re.match(self.storm_mov[0])
			if wmo_dir_speed_m:
				self.wmo_dir = wmo_dir_speed_m.groups()[1].strip()
				self.wmo_dirn = self.__dirnotation[int(self.wmo_dir)]
				self.wmo_speed = wmo_dir_speed_m.groups()[2].strip()

	def parse_maxswww_header(self):
		if self.maxswww:
			maxswww_m = self.__max_swww_re.match(self.maxswww[0])
			if maxswww_m:
				self.msw = maxswww_m.groups()[0].strip()
				self.gusts = maxswww_m.groups()[1].strip()
				#print self.msw, self.gusts

	def parse_fvalid_header(self):
		if self.fvalid_header:
			for fi in self.fvalid_header:
				#print fi
				fi_m = self.__fvalid_re.match(fi[0])
				fvi, fviw = None, None
				if fi_m:
					fvi = fi_m.groups()
					#self.fvalid.append(fvi)
					#print fvi
				fiw_m = self.__max_fo_re.match(fi[1])
				if fiw_m:
					fviw = fiw_m.groups()
				if fvi and fviw:
						#print fvi
						lat, latd = fvi[1], fvi[2]
						lon, lond = fvi[3], fvi[4]					
						ctime = fvi[0]
						mw, mg = fviw[0], fviw[2]	
						fvo = ForecastValid(lat, latd, lon, lond, ctime, mw,mg)
						self.fvalid.append(fvo)

	def parse_ovalid_header(self):
		if self.ovalid_header:
			for oi in self.ovalid_header:
				oi_m = self.__ovalid_re.match(oi[0])
				if oi_m:
					ovi = oi_m.groups()
					#self.ovalid.append(ovi)
				oiw_m = self.__max_fo_re.match(oi[1])
				if oiw_m:
					oviw = oiw_m.groups()
				if ovi and oviw:
						#print fvi
						lat, latd = ovi[1], ovi[2]
						lon, lond = ovi[3], ovi[4]					
						ctime = ovi[0]
						mw, mg = oviw[0], oviw[2]	
						ovo = OutlookValid(lat, latd, lon, lond, ctime, mw,mg)
						self.ovalid.append(ovo)

	def generate_tropical_adv_all(self):
		if self.hr_st_type is not None:
			hrst_fname = "%s %s %s" % (self.hr_st_type, self.cy_or_st, self.hr_st_name)	
		else:
			hrst_fname = "%s %s" % (self.cy_or_st, self.hr_st_name)	
		loc_coord = "%s%s / %s%s" % (self.lat, self.latd, self.lon, self.lond)
		ta_name_center = "%s. Center located near %s at %s. " % (hrst_fname, loc_coord, self.ctime)
		ta_mov = "Present movement toward %s at %sKT Max winds %s/%sKT. " % (self.wmo_dir, self.wmo_speed, self.msw, self.gusts)
		ta_forecast = ""
		for fvi in self.fvalid:
			#print fvi
			#ta_fi = "Forecast %s %s%s/%s%s. " % (fvi[0],fvi[1],fvi[2],fvi[3],fvi[4])
			ta_forecast = ta_forecast + fvi.get_fv_text()

		ta_outlook = ""
		for ovi in self.ovalid:
			#ta_fi = "Outlook %s %s%s/%s%s. " % (ovi[0],ovi[1],ovi[2],ovi[3],ovi[4])
			ta_outlook = ta_forecast + ovi.get_ov_text()

		tropical_adv = ta_name_center + ta_mov + ta_forecast + ta_outlook
		return tropical_adv

	def generate_tropical_adv(self):
		if self.hr_st_type:
			hrst_fname = "%s %s %s" % (self.hr_st_type, self.cy_or_st, self.hr_st_name)
		else:
			hrst_fname = "%s %s" % (self.cy_or_st, self.hr_st_name)
		loc_coord = "%s%s/%s%s" % (self.lat, self.latd, self.lon, self.lond)
		ta_name_center = "%s. Center located near %s at %s. " % (hrst_fname, loc_coord, self.ctime)
		ta_mov = "Present movement toward %s at %sKT Max winds %s/%sKT. " % (self.wmo_dirn, self.wmo_speed, self.msw, self.gusts)
		tropical_adv = ta_name_center + ta_mov

		if self.fvalid:
			ta_forecast = self.fvalid[len(self.fvalid)-1].get_fv_text()
			#print ta_forecast
			tropical_adv = tropical_adv + ta_forecast
		if self.ovalid:
			ta_outlook = self.ovalid[0].get_ov_text()
			tropical_adv = tropical_adv + ta_outlook

		return tropical_adv

	def parse_headers(self):
		self.parse_wmo_header()
		self.parse_storm_loc_header()
		self.parse_storm_mov_header()
		self.parse_maxswww_header()
		self.parse_fvalid_header()
		self.parse_ovalid_header()


	def get_current_state(self):
		features = []
		ffeatures = []
		ofeatures = []
		for fvi in self.fvalid:
			# coordinates order [longitude, latitude, elevation]
			tlat, tlon = float(fvi.lat), float(fvi.lon)
			glat, glon = tlat, tlon
			if fvi.latd=='S':
				glat = -tlat
			if fvi.lond=='W':
				glon = 360 - tlon
				glon = glon%360
			fvi_geom = { "type":"Point", "coordinates":[glon, glat]}
			fvi_prop =  {"lat":tlat, "latd":fvi.latd, "lon":tlon , "lond":fvi.lond, "time": fvi.ftime, "maxwinds": int(fvi.maxwind) , "gusts": int(fvi.maxgusts) }
			fvi_feature = {"type":"Feature", "geometry": fvi_geom, "properties": fvi_prop}
			ffeatures.append(fvi_feature)

		for ovi in self.ovalid:
			# coordinates order [longitude, latitude, elevation]
			tlat, tlon = float(ovi.lat), float(ovi.lon)
			glat, glon = tlat, tlon
			if ovi.latd=='S':
				glat = -tlat
			if ovi.lond=='W':
				glon = 360 - tlon
				glon = glon%360
			ovi_geom = { "type":"Point", "coordinates":[glon, glat]}
			ovi_prop =  {"lat":tlat, "latd":ovi.latd, "lon":tlon , "lond":ovi.lond , "time": ovi.ftime, "maxwinds": int(ovi.maxwind) , "gusts": int(ovi.maxgusts) }
			ovi_feature = {"type":"Feature", "geometry": ovi_geom, "properties": ovi_prop}
			ofeatures.append(ovi_feature)

		fvfc = {"type":"FeatueCollection", "features":ffeatures}
		ovfc = {"type":"FeatueCollection", "features":ofeatures}
		#fc = {"type":"FeatureCollection", "features" : features}
		fc_prop = {}
		fc_prop['forecast'] = fvfc
		fc_prop['outlook'] = ovfc
		fc_prop['tc_id'] = self.tc_id
		fc_prop['adv_num'] = int(self.hr_st_adv_num)
		fc_prop['type'] = self.hr_st_type
		fc_prop['source'] = "NHC"
		fc_prop['cy_or_st'] = self.cy_or_st
		fc_prop['name'] = self.hr_st_name
		fc_prop['location'] = {'lat': float(self.lat), 'latd':self.latd, 'lon':float(self.lon), 'lond':self.lond}
		fc_prop['time'] = self.ctime
		fc_prop['movement'] = {'dir':int(self.wmo_dir), 'dirn':self.wmo_dirn, 'speed':int(self.wmo_speed), 'msw':int(self.msw), 'gusts':int(self.gusts)}
		#fc['properties'] = fc_prop
		#json_fc = json.dumps(fc)
		json_fc = json.dumps(fc_prop)
#		trpadv_path = '/syndata/trpcl_adv'
#		trpcl_adv_path
		jsonf_path = os.path.join(trpadv_path,'ALERTS',"%s.json" % self.tc_id)
		with open(jsonf_path, "w") as jsonf:
			jsonf.write(json_fc)

		return features
