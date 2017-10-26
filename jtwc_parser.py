import requests
import re
import datetime
from rangedict import RangeDict
import os
import json
from trpcl_adv_fpath import *

class ForecastValid:
	__dir_map = {(0.00, 11.25): 'N',(11.25, 33.75): 'NNE', (33.75, 56.25): 'NE',(56.25, 78.75): 'ENE', (78.75, 101.25): 'E',
		(101.25, 123.75): 'ESE', (123.75, 146.25): 'SE', (146.25, 168.75): 'SSE',  (168.75, 191.25): 'S',
		(191.25, 213.75): 'SSW', (213.75, 236.25): 'SW', (236.25, 258.75): 'WSW', (258.75, 281.25): 'W',
		(281.25, 303.75): 'WNW',(303.75, 326.25): 'NW',(326.25, 348.75): 'NNW', (348.75, 361.00): 'N'}

	__dirnotation = RangeDict(__dir_map)

	def __init__(self, fvargs):
		self.typh_mov_speed = None
		self.typh_mov_dir = None
		self.typh_mov_dirn = None
		self.typh_mov_speed_unit = None

		if 'lat' in fvargs:		
			self.lat  = fvargs['lat']
		if 'latd' in fvargs:		
			self.latd  = fvargs['latd']
		if 'lon' in fvargs:		
			self.lon  = fvargs['lon']
		if 'lond' in fvargs:
			self.lond  = fvargs['lond']
		if 'attime' in fvargs:
			self.ftime = fvargs['attime']
		if 'max_stnd_wind' in fvargs:
			self.maxwind = fvargs['max_stnd_wind']
		if 'gusts' in fvargs:
			self.maxgusts = fvargs['gusts']

		if 'm_speed' in fvargs:
			self.typh_mov_speed = fvargs['m_speed']
		if 'm_dir' in fvargs:
			self.typh_mov_dir = fvargs['m_dir'].strip()
			self.typh_mov_dirn = self.__dirnotation[int(self.typh_mov_dir)]
		if 'm_spd_unit' in fvargs:
			self.typh_mov_speed_unit = fvargs['m_spd_unit']


	def format_time(self, itime):
		return self.ftime[:2] + '/' + self.ftime[2:]

	def get_fv_text(self):
		return "Forecast %s %s%s/%s%s Max winds %s/%s KT. " % (self.format_time(self.ftime), self.lat, self.latd, self.lon, self.lond, self.maxwind, self.maxgusts)

	def get_center_text(self):
		#return "Forecast %s %s%s/%s%s Max winds %s/%s KT. " % (self.format_time(self.ftime), self.lat, self.latd, self.lon, self.lond, self.maxwind, self.maxgusts)
		return "Center located near %s%s/%s%s at %s." % (self.lat, self.latd, self.lon, self.lond, self.format_time(self.ftime))

	def get_mov_text(self):
		return "Present movement toward %s at %s KT Max winds %s/%s KT." % (self.typh_mov_dirn, self.typh_mov_speed,self.maxwind, self.maxgusts)

	def get_json(self):
		lat, lon, ctime = None, None, None
		if latd=='S':
			lat = -self.lat
		if lond=='W':
			lon=360 - lon
			lon=lon%360

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


class JTWCForecastAdvisoryParser():
	#WTPN31 PGTW 152100
	__id_re = re.compile("\s*(?P<tc_id>.*)\s+(?P<id_type>.*)\s+(?P<o_num>.*)\s*\r\n")
	__section_separator_re = re.compile("\s*(---)\s*")

	__jtwc_start_re = re.compile("(?P<seq_num>\d*)\.\s*(?P<type>.*\s)?(?P<kind>HURRICANE|CYCLONE|STORM|DEPRESSION|DISTURBANCE|TYPHOON|REMNANTS)\s+(?P<name>.*)\s+(WARNING)\s+NR\s+(?P<number>.*)")

	__warning_pos_header_re = re.compile("\s*WARNING\s*POSITION\s*:\r\n")
	__warning_loc_re = re.compile("\s*(?P<attime>.*)\s+---\s+(?P<other>.*)\s+(?P<lat>\d*.\d*)(?P<latd>N|S)\s+(?P<lon>\d*.\d*)(?P<lond>E|W)\r\n")

	__movment_re = re.compile("\s*MOVEMENT\s+PAST\s+(?P<m_past_hrs>.*)HOURS\s*-\s*(?P<m_dir>\d*)\s+DEGREES\s+AT\s+(?P<m_speed>.*)\s+(?P<m_spd_unit>.*)\s*(?P<m_cat>QUASI|STATIONARY|ERRATIC)?\s*(?P<m_other_info>.*)?\r\n")
	__mov_acc_re = re.compile("\s*POSITION\s+ACCURATE\s+TO\s+WITHIN\s+(?P<pos_acc>\d*)\s+(?P<pos_acc_unit>.*)\r\n")
	__max_sstnd_winds_re = re.compile("\s*MAX\s+SUSTAINED\s+WINDS\s+-\s+(?P<max_stnd_wind>\d*)\s+KT,\s+GUSTS\s+(?P<gusts>\d*)\s+KT\s*\r\n")

	__forecasts_re = re.compile("\s*(?P<forecasts>FORECASTS)\s*:\s*\r\n")
	__fvalid_re = re.compile("\s*(?P<valid_at_hrs>\d*)\s*HRS,\s*VALID\s*AT\s*:\s*\r\n")
	__fvalid_tll_re = re.compile("\s*(?P<attime>.*)\s+---\s*(?P<lat>\d*.\d*)(?P<latd>N|S)\s+(?P<lon>\d*.\d*)(?P<lond>E|W)\s*\r\n")

	__extended_outlook_re = re.compile("\s*(?P<forecasts>EXTENDED OUTLOOK)\s*:\s*\r\n")
	__longrange_outlook_re = re.compile("\s*(?P<forecasts>FORECASTS)\s*:\s*\r\n")

	__dir_map = {(0.00, 11.25): 'N',(11.25, 33.75): 'NNE', (33.75, 56.25): 'NE',(56.25, 78.75): 'ENE', (78.75, 101.25): 'E',
		(101.25, 123.75): 'ESE', (123.75, 146.25): 'SE', (146.25, 168.75): 'SSE',  (168.75, 191.25): 'S',
		(191.25, 213.75): 'SSW', (213.75, 236.25): 'SW', (236.25, 258.75): 'WSW', (258.75, 281.25): 'W',
		(281.25, 303.75): 'WNW',(303.75, 326.25): 'NW',(326.25, 348.75): 'NNW', (348.75, 361.00): 'N'}

	__dirnotation = RangeDict(__dir_map)


	def __init__(self,**kwargs):
		self.tc_id = None
		self.jtwc_header = None 			# WMO Header
		self.wwn = ""					# Watches/Warnings and News
		self.typh_kind = None
		self.typh_type = None
		self.typh_name = None
		self.typh_adv_number = None
		self.typh_cuurent_loc = None
		self.typh_lat = None
		self.typh_latd = None
		self.typh_lon = None
		self.typh_lond = None
		self.typh_mov_speed = None
		self.typh_mov_dir = None
		self.typh_mov_dirn = None
		self.typh_mov_speed_unit = None
		self.typh_max_wnd = None
		self.typh_gusts = None
		self.storm_loc = []				# Storm Location
		self.storm_mov = []				# Storm Movement
		self.mcp = "" 					# Minimum Central Pressure
		self.ese= ""					# Eye Size Estimate
		self.maxswww = [] 				# Max Sustained Wind, Wind Radii, and 12-Foot Wave Height Radii Section Repeat
		self.fvalid_header = []
		self.ovalid_header = []
		self.ovalid = []
		self.fvalid = []
		self.fs_rsr = "" 				# Request for Ship Reports
		self.next_adv = "" 				# Next Advisory
		self.text_forecastf = None
		if 'filename' in kwargs:
			self.text_forecastf = kwargs['filename']	
			#print self.text_forecastf


	def get_textforecastf(self):
		if self.text_forecastf:
			return self.text_forecastf
		return None

	def __set_typh_ids(self, parai):
		#print parai
		if 'tc_id' in parai:
			self.tc_id = parai['tc_id']
		if 'id_type' in parai:
			self.if_type = parai['id_type']
		if 'o_num' in parai:
			self.o_num = parai['o_num']

	def __set_typh_para(self, parai):
		#print parai
		if 'kind' in parai:
			self.typh_kind = parai['kind']
		if 'type' in parai:
			self.typh_type = parai['type']
		if 'name' in parai:
			self.typh_name = parai['name']
		if 'number' in parai:
			if parai['number']:
				self.typh_adv_number = parai['number'].strip()
		#print self.typh_type, self.typh_kind, self.typh_name

	def __set_typh_location(self, parai):		
		if 'lat' in parai:
			self.typh_lat = parai['lat']
		if 'latd' in parai:
			self.typh_latd = parai['latd']
		if 'lon' in parai:
			self.typh_lon = parai['lon']
		if 'lond' in parai:
			self.typh_lond = parai['lond']
		if 'attime' in parai:
			self.typh_time = parai['attime']
		#print self.typh_lat, self.typh_latd, self.typh_lon, self.typh_lond, self.typh_time

	def __set_typh_movment(self, parai):
		if 'm_speed' in parai:
			self.typh_mov_speed = parai['m_speed']
		if 'm_dir' in parai:
			self.typh_mov_dir = parai['m_dir'].strip()
			self.typh_mov_dirn = self.__dirnotation[int(self.typh_mov_dir)]
		if 'm_spd_unit' in parai:
			self.typh_mov_speed_unit = parai['m_spd_unit']
		#print self.typh_mov_dir, self.typh_mov_dirn, self.typh_mov_speed,self.typh_mov_speed_unit

	def __set_typh_max_wind(self, max_wind_para):		
		if 'max_stnd_wind' in max_wind_para:
			self.typh_max_wnd = max_wind_para['max_stnd_wind']
		if 'gusts' in max_wind_para:
			self.typh_gusts = max_wind_para['gusts']		

	def format_time(self, itime):
		return self.typh_time[:2] + '/' + self.typh_time[2:]

	def get_adv(self):
		if self.typh_type :		
			typh_fname = "%s %s %s" % (self.typh_type, self.typh_kind, self.typh_name)
		else:
			typh_fname = "%s %s" % (self.typh_kind, self.typh_name)
		loc_coord = "%s%s/%s%s" % (self.typh_lat, self.typh_latd, self.typh_lon, self.typh_lond)
		#ta_name_center = "%s. Center located near %s at %s. " % (typh_fname, loc_coord, self.format_time(self.typh_time))
		#ta_mov = "Present movement toward %s at %s KT Max winds %s/%s KT. " % (self.typh_mov_dirn, self.typh_mov_speed, self.typh_max_wnd, self.typh_gusts)
		ta_name_center = self.typh_cuurent_loc.get_center_text()
		ta_mov = self.typh_cuurent_loc.get_mov_text()
		tropical_adv = ta_name_center + ' '+ ta_mov

		ta_forecast = ''
		if self.fvalid:
			total_fv = len(self.fvalid)
			mid_fv = (total_fv+1)/2
			last_fv = (total_fv-1)
			ta_forecast = ta_forecast + ' ' + self.fvalid[mid_fv].get_fv_text() 
			ta_forecast = ta_forecast + self.fvalid[last_fv].get_fv_text() 
		tropical_adv = tropical_adv + ta_forecast
		
		return tropical_adv

	def set_paras(self):
		if self.text_forecastf:
			#with open(os.path.join("FAs","IOC",self.text_forecastf),'r') as far:
			with open(self.text_forecastf,'r') as far:
				lines = far.readlines()
				#self.wmo_header = [line.replace('\n', '') for line in lines[:7]]
				bline_count = 0
				lindex = 0
				total_lines = len(lines)
				found_header = False
				found_section = False
				is_eof = False
				id_m = self.__id_re.match(lines[0])
				if id_m:
					ids_d = id_m.groupdict()
					self.__set_typh_ids(ids_d)
				while (not found_header) and (not is_eof):				
					jtwc_m = self.__jtwc_start_re.match(lines[lindex].replace('\r\n',''))
					if jtwc_m:
						found_header = True
						jtwc_header = jtwc_m.groupdict()
						self.__set_typh_para(jtwc_header)						
					lindex = lindex + 1
					if lindex >= total_lines:
						is_eof = True
				#print lindex
				found_section = False
				is_eof = False				
				while (not found_section) and (not is_eof):					
					warning_s_m = self.__warning_pos_header_re.match(lines[lindex])
					if warning_s_m is not None:
						warn_header = warning_s_m.groups()						
						found_section = True
					lindex = lindex + 1	
					if lindex >= total_lines:
						is_eof = True
				#print lindex
				found_section = False
				is_eof = False				
				while (not found_section) and (not is_eof):					
					warning_loc_m = self.__warning_loc_re.match(lines[lindex])
					if warning_loc_m is not None:
						warn_loc = warning_loc_m.groupdict()
						self.__set_typh_location(warn_loc)
						found_section = True
					lindex = lindex + 1	
					if lindex >= total_lines:
						is_eof = True					

				found_section = False
				is_eof = False				
				while (not found_section) and (not is_eof):					
					mov_m = self.__movment_re.match(lines[lindex])
					if mov_m is not None:
						mov = mov_m.groupdict()						
						self.__set_typh_movment(mov)
						found_section = True
					lindex = lindex + 1	
					if lindex >= total_lines:
						is_eof = True					

				found_section = False
				is_eof = False				
				while (not found_section) and (not is_eof):					
					mov_acc_m = self.__mov_acc_re.match(lines[lindex])
					if mov_acc_m is not None:
						mov_acc = mov_acc_m.groupdict()
						#print mov_acc
						found_section = True
					lindex = lindex + 1	
					if lindex >= total_lines:
						is_eof = True					

				found_section = False
				is_eof = False				
				while (not found_section) and (not is_eof):					
					max_sstnd_m = self.__max_sstnd_winds_re.match(lines[lindex])
					if max_sstnd_m is not None:
						max_sstnd = max_sstnd_m.groupdict()						
						self.__set_typh_max_wind(max_sstnd)		
						found_section = True
					lindex = lindex + 1	
					if lindex >= total_lines:
						is_eof = True					

				tth_cloc = dict(warn_loc.items() + max_sstnd.items() + mov.items())
				self.typh_cuurent_loc = ForecastValid(tth_cloc)
				#print self.typh_cuurent_loc.get_fv_text()				
				#print self.typh_cuurent_loc.get_mov_text()

				found_section = False
				is_eof = False				
				while (not found_section) and (not is_eof):					
					forecasts_m = self.__forecasts_re.match(lines[lindex])
					if forecasts_m is not None:
						fcsts = forecasts_m.groups()
						#print fcsts
						found_section = True
					lindex = lindex + 1	
					if lindex >= total_lines:
						is_eof = True					

				fvalids = []
				found_section = False
				found_all_fvalid = False
				is_eof = False				
				while (not found_section) and (not is_eof) and (not found_all_fvalid):
					fvalid_m = self.__fvalid_re.match(lines[lindex])
					if fvalid_m is not None:
						fvi = fvalid_m.groupdict()						
						lindex = lindex + 1
						fvalid_tll_m = self.__fvalid_tll_re.match(lines[lindex])
						fvalid_tll = fvalid_tll_m.groupdict()
						lindex = lindex + 1
						fvalid_max_sstnd_m = self.__max_sstnd_winds_re.match(lines[lindex])
						fvalid_max_sstnd = fvalid_max_sstnd_m.groupdict()					
						fvalid_all = dict(fvi.items() + fvalid_tll.items() + fvalid_max_sstnd.items())
						fvalido = ForecastValid(fvalid_all)
						self.fvalid.append(fvalido)
						#print fvalido.get_fv_text()
						#print fvalid
						#print fvalid_tll
						#print fvalid_max_sstnd
					lindex = lindex + 1
					if lindex >= total_lines:
						is_eof = True

				#print len(fvalids)


			##print self.storm_loc

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
			ovi_prop =  {"lat":tlat, "latd":ovi.latd, "lon":tlon , "lond":ovi.lond , "time": ovi.ftime,  "maxwinds": int(ovi.maxwind) , "gusts": int(ovi.maxgusts) }
			ovi_feature = {"type":"Feature", "geometry": ovi_geom, "properties": ovi_prop}
			ofeatures.append(ovi_feature)

		fvfc = {"type":"FeatueCollection", "features":ffeatures}
		ovfc = {"type":"FeatueCollection", "features":ofeatures}
		#fc = {"type":"FeatureCollection", "features" : features}
		fc_prop = {}
		fc_prop['source'] = "JTWC"
		fc_prop['forecast'] = fvfc
		fc_prop['outlook'] = ovfc
		fc_prop['tc_id'] = self.tc_id
		fc_prop['adv_num'] = int(self.typh_adv_number)
		fc_prop['type'] = self.typh_type
		fc_prop['cy_or_st'] = self.typh_kind
		fc_prop['name'] = self.typh_name
		#self.typh_cuurent_loc.lat
		fc_prop['location'] = {'lat': float(self.typh_cuurent_loc.lat), 'latd':self.typh_cuurent_loc.latd, 'lon':float(self.typh_cuurent_loc.lon), 'lond':self.typh_cuurent_loc.lond}
		fc_prop['time'] = self.typh_cuurent_loc.ftime #self.ctime 
		fc_prop['movement'] = {'dir':int(self.typh_mov_dir), 'dirn':self.typh_mov_dirn, 'speed':int(self.typh_mov_speed), 'msw':int(self.typh_cuurent_loc.maxwind), 'gusts':int(self.typh_cuurent_loc.maxgusts)}
		#fc['properties'] = fc_prop
		#json_fc = json.dumps(fc)
		json_fc = json.dumps(fc_prop)
		#trpadv_path = '/syndata/trpcl_adv'
		#trpcl_adv_path
		jsonf_path = os.path.join(trpadv_path,'ALERTS',"%s.json" % self.tc_id)
		#jsonf_path = os.path.join('FAs','ALERTS',"%s.json" % self.tc_id)
		with open(jsonf_path, "w") as jsonf:
			jsonf.write(json_fc)

		return features
