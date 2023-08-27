"""
LICENCE:
This parser was written by aceisace and as such, does not belong to epdiy or is associated with epdiy in any way, but may be used for development as long as you publish any progress you have made back to me.

Copyright by aceisace [Github]
"""
import json
import logging
import os
import struct
from enum import IntEnum
from pprint import pprint
from typing import List

import numpy

logger = logging.getLogger(__name__)


class EPD_MODE(IntEnum):
	INIT = 0
	DU = 1
	GC16 = 2
	GC16_FAST = 3
	A2 = 4
	GL16 = 5
	GL16_FAST = 6
	DU4 = 7
	REAGL = 8
	REAGLD = 9
	GL4 = 10
	GL16_INV = 11


class WaveFormHeader:

	def __init__(self, file_data):
		CHECKSUM, FILESIZE, SERIAL, \
		RUN_TYPE, FPL_PLATFORM, \
		FPL_LOT, \
		MODE_VERSION, WF_VERSION, WF_SUBVERSION, WF_TYPE, \
		FPL_SIZE, MFG_CODE, WFM_REV, FRAME_RATE, \
		UNKNOWN1, VCOM_OFFSET, \
		UNKNOWN2, \
		XWIA1, XWIA2, XWIA3, \
		CS1, \
		WMTA1, WMTA2, WMTA3, \
		FVSN, LUTS, MC, TRC, \
		FLAGS, EB, SB, \
		RESERVED1, RESERVED2, RESERVED3, RESERVED4, \
		RESERVED5, CS2 \
			= struct.unpack(
			"<L L L \
			B B \
			H \
			B B B B \
			B B B B \
			B B \
			H \
			B B B \
			B\
			B B B\
			B B B B \
			B B B \
			B B B B \
			B B", file_data[:48])

		XWIA = (XWIA3 << 16) + (XWIA2 << 8) + XWIA1
		XWIA_LENGTH = file_data[XWIA]
		HDR_SIZE = XWIA + XWIA_LENGTH + 2

		all_variables = locals()

		self.all_vars = {
			key: value for key, value in all_variables.items() if
			key not in ("self", "header_section", "__len__")
		}

	def get_data(self):
		return self.all_vars

	def __repr__(self):
		header = self.get_data()
		return (f"""
			CHECKSUM : {header["CHECKSUM"]}
			FILESIZE: {header["FILESIZE"]}
			SERIAL : {header["SERIAL"]}
			RUN_TYPE : {hex(header["RUN_TYPE"])}
			FPL_PLATFORM : {header["FPL_PLATFORM"]}
			FPL_LOT : {header["FPL_LOT"]}
			MODE_VERSION : {header["MODE_VERSION"]}
			WF_VERSION : {header["WF_VERSION"]}
			WF_SUBVERSION : {header["WF_SUBVERSION"]}
			WF_TYPE : {hex(header["WF_TYPE"])}
			FPL_SIZE : {header["FPL_SIZE"]}
			MFG_CODE : {header["MFG_CODE"]}
			WFM_REV : {header["WFM_REV"]}
			FRAME_RATE : {hex(header["FRAME_RATE"])[2:]} Hz
			VCOM_OFFSET : {header["VCOM_OFFSET"]}
			XWIA : {header["XWIA"]} (LENGTH: {header["XWIA_LENGTH"]})
			CS1 : {hex(header["CS1"])}"
			WMTA :  Not implemented
			FVSN : {hex(header["FVSN"])}
			LUTS : {hex(header["LUTS"])}
			MC : {header["MC"]} (Mode count)
			TRC : {header["TRC"]} (temperature range count)
			FLAGS : {header["FLAGS"]}
			EB : {hex(header["EB"])}
			SB : {hex(header["SB"])}
			RESERVED : {header["RESERVED1"]} {header["RESERVED2"]} {header["RESERVED3"]} {header["RESERVED4"]} {header["RESERVED5"]}
			CS2 : {hex(header["CS2"])}

			BITS_PER_PIXEL = {(4, 5)[header["LUTS"] & 0xC == 4]}
			NUMBER_OF_WAVEFORMS = {header["MC"] + 1}
			NUMER_OF_TEMPERATURE_RANGES = {header["TRC"] + 1}

			FILENAME = {header["filename"]}
			""")


class WaveFormParser:
	def __init__(self, path: str):
		self.path = path
		self.header_size = 48
		self.MAX_WAVEFORMS = 4096

		self.header = {}
		self.modes = {}
		self.possible_temperature_ranges = {}
		self.temperature_ranges = {}
		self.waveforms = {}
		self.waveform_addresses = [0] * self.MAX_WAVEFORMS

		logger.info("loading waveform")
		with open(filepath, "rb") as file:
			self.data = file.read()

		self.parse_header()

		calculated_filesize = os.stat(self.path).st_size
		if calculated_filesize == self.header["FILESIZE"]:
			logger.info("filesize check passed")

		self.get_temperature_ranges()
		self.get_modes()
		self.populate_temperature_addresses()
		self.unique_waveforms = len([_ for _ in self.waveform_addresses if _ != 0])
		self.get_waveforms()
		logger.info(f"Found a total of {self.unique_waveforms} waveforms")

	def parse_header(self):
		self.header = WaveFormHeader(self.data).get_data()

	def get_modes(self):
		mode_start = self.data[self.header["HDR_SIZE"]:]

		for _ in range(self.header["MC"] + 1):
			self.modes[_] = {}
			address, mode_checksum = self.get_addr_and_checksum(mode_start)
			checksum = (mode_start[0] + mode_start[1] + mode_start[2]) & 0xFF
			if checksum != mode_checksum:
				logger.error("FAILED!")
			self.modes[_]["name"] = EPD_MODE(_).name
			self.modes[_]["address"] = address
			mode_start = mode_start[4:]

	def get_temperature_ranges(self):
		for index, i in enumerate(range(self.header["TRC"] + 1)):
			# print(f"Range {index}: from {numpy.uint8(data[48:][i])} to {numpy.uint8(data[48:][i + 1])} °C")
			self.possible_temperature_ranges[i] = range(numpy.uint8(self.data[48:][i]), numpy.uint8(self.data[48:][
																										i + 1]))  # f"{numpy.uint8(self.data[48:][i])} C - {numpy.uint8(self.data[48:][i + 1])} C"

	# self.temperature_ranges_dict[i]

	@staticmethod
	def get_addr_and_checksum(input_data) -> tuple:
		address_low, address_high, checksum = struct.unpack("HBB", input_data[:struct.calcsize("HBB")])
		addr = address_high << 16 | address_low
		return addr, checksum

	@staticmethod
	def calculate_checksum(input_data):
		return (input_data[0] + input_data[1] + input_data[2]) & 0xFF

	@staticmethod
	def merge_2_bytes(byte1, byte2):
		return (byte2 << 8) + byte1

	@staticmethod
	def merge_3_bytes(byte1, byte2, byte3):
		return (byte3 << 16) + (byte2 << 8) + byte1

	def get_waveform_length(self, waveform_address):
		for _ in range(self.MAX_WAVEFORMS - 1):
			if self.waveform_addresses[_] == waveform_address:
				if not self.waveform_addresses[_]:
					return 0
				return self.waveform_addresses[_ + 1] - waveform_address
		return 0

	@staticmethod
	def add_addr(all_addresses, current_addresses, maximum_range: int):
		for i in range(0, maximum_range):
			if all_addresses[i] == current_addresses:
				return
			if not all_addresses[i]:
				all_addresses[i] = current_addresses
				break

	def populate_temperature_addresses(self):
		for key, values in self.modes.items():
			self.temperature_ranges[f"{values['name']}"] = {}

			# populate waveform-addresses
			data_start = self.data[values["address"]:]
			for _ in range(0, self.header["TRC"] + 1):
				self.temperature_ranges[f"{values['name']}"][_] = {}
				self.temperature_ranges[f"{values['name']}"][_]["range"] = self.possible_temperature_ranges[_]
				address, checksum = self.get_addr_and_checksum(data_start)
				calculated_checksum = (data_start[0] + data_start[1] + data_start[2]) & 0xFF
				if checksum != calculated_checksum:
					logger.error("FAILED!")
				self.temperature_ranges[f"{values['name']}"][_]["address"] = address

				self.add_addr(
					all_addresses=self.waveform_addresses, current_addresses=address, maximum_range=self.MAX_WAVEFORMS)
				data_start = data_start[4:]

	@staticmethod
	def get_phases(num: int):
		phase1 = num & 0b11
		phase2 = (num >> 2) & 0b11
		phase3 = (num >> 4) & 0b11
		phase4 = (num >> 6) & 0b11
		return [phase1, phase2, phase3, phase4]

	@staticmethod
	def get_phases_4(nums: List[int]):
		phases = []
		for num in nums:
			phase = num & 0b11, (num >> 2) & 0b11, (num >> 4) & 0b11, (num >> 6) & 0b11
			phases.extend(phase)
		return phases

	def get_waveforms(self):
		for mode_name, mode_data in self.temperature_ranges.items():
			self.waveforms[EPD_MODE[mode_name].value] = {}
			current_mode = self.waveforms[EPD_MODE[mode_name].value]
			for temperature_range, temperature_data in mode_data.items():
				current_mode[self.possible_temperature_ranges[temperature_range]] = {}
				current_combi = current_mode[self.possible_temperature_ranges[temperature_range]]
				address = temperature_data["address"]
				waveform_length = self.get_waveform_length(address) - 2
				waveform_start = self.data[address:]

				active, index = False, 0

				curr_waveform = []
				while index < waveform_length - 1:

					end_reached = bool(waveform_start[index] == 0xFC)  # 0xfc is end-signal
					if end_reached:
						active = not active
						index += 1
					else:
						curr_waveform.append(waveform_start[index])
						if active:  # 1-byte pattern
							index += 1
						else:  # 2-byte pattern (second byte is count)
							index += 2

				current_combi["waveform_hex"] = [hex(_)[2:] for _ in curr_waveform]
				current_combi["phases"] = [self.get_phases(_) for _ in curr_waveform]
				current_combi["length"] = waveform_length

	def to_json_epdiy(self, filter_modes=List[EPD_MODE]):
		temperature_part = {
			"temperature_ranges": {
				"range_bounds": []}}
		for key, value in self.possible_temperature_ranges.items():
			temperature_part["temperature_ranges"]["range_bounds"].append(
				{
					"from": value.start,
					"to": value.stop})

		filter_mode_names = [str(_).split(".")[-1] for _ in filter_modes]

		modes = [{
			"mode": mode_name,
			"ranges": [{
				"index": t,
				"phases": []} for t in self.possible_temperature_ranges]
		} for mode_name, values in self.waveforms.items()]

		mode_counter = 0
		for mode_name, mode_data in self.waveforms.items():
			# if mode_name not in filter_mode_names:
			# 	del optimised[mode_name]
			current_mode = self.waveforms[mode_name]
			temp_count = 0
			for temperature_range, temperature_data in mode_data.items():
				current_phases = current_mode[temperature_range]["phases"]
				grouped_list = [current_phases[i:i + 4] for i in range(0, len(current_phases), 4)]
				combined_list = [[item for sublist in group for item in sublist] for group in grouped_list]
				if combined_list and len(combined_list[-1]) != 16:
					combined_list[-1] += [0]*(16-len(combined_list[-1]))
				modes[mode_counter]["ranges"][temp_count]["phases"] = combined_list
				temp_count += 1
			mode_counter += 1
		return json.dumps({"temperature_ranges": temperature_part["temperature_ranges"], "modes": modes})


if __name__ == '__main__':
	logging.basicConfig(level=logging.DEBUG)
	filepath = "waveform.wbf"

	parser = WaveFormParser(filepath)
	waveforms = parser.waveforms
	pprint(waveforms, sort_dicts=False, width=200, compact=True)
	print("completed")
