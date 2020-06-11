#!/usr/bin/env python


import datetime
import requests
import settings
import telebot
import json
import sys

from bs4 import BeautifulSoup


class PageActions():
	def __init__(self):
		self.direct = f'{settings.TEMP_DIR}'
		self.url = settings.URL
		self.send = PushNotify()

	def get_page(self):
		with open(f'{self.direct}page.html', 'wb') as page:
			page.write(requests.get(self.url).content)

	def parse_page(self):
		rate = []
		with open(f'{self.direct}page.html', 'r') as page:
			content = BeautifulSoup(page.read(), 'lxml')
			for divs in content.find_all('div', class_='kurs-bar__item'):
				for tags in divs.tbody.find_all('tr'):
					for x in tags.text.split():
						rate.append(x)
		return rate

	def log_write(self, lst):
		with open(f'{self.direct}log.json', 'w') as file:
			file.write(json.dumps(lst))


class DataPrepare(PageActions):
	DICT_VALUES = {}

	def grep_values(self):
		values_page= self.parse_page()
		rate_values = [ values_page[18:30] [i:i + 2] for i in range(0, len(values_page[18:30]), 2) ] 	
		index_val = 0 
		for nom in values_page[:6]:
			self.DICT_VALUES[nom] = rate_values[index_val]
			index_val += 1

	def compare_purchase(self):
		with open(f'{self.direct}log.json', 'r') as log:
			compare_val = json.load(log)
			for new_value in self.DICT_VALUES.items():
				old_value = compare_val.get(new_value[0])
				if new_value[1][0] > old_value[0]:
					result = float(new_value[1][0]) - float(old_value[0])
					sale = self.compare_sale(new_value[1][1], old_value[1])
					self.send.message_prepare(f"{new_value[0].upper()}: {new_value[1][0]} \u2191", sale)
				elif new_value[1][0] == old_value[0]:
					sale = self.compare_sale(new_value[1][1], old_value[1])
					self.send.message_prepare(f"{new_value[0].upper()}: {new_value[1][0]}", sale)
				else:
					result = float(old_value[0]) - float(new_value[1][0])
					sale = self.compare_sale(new_value[1][1], old_value[1])
					self.send.message_prepare(f"{new_value[0].upper()}: {new_value[1][0]} \u2193", sale)
			return self.send.msg

	def compare_sale(self, new_value, old_value):
		if new_value > old_value:
			result = float(new_value) - float(old_value)
			return f"{new_value} \u2191"
		elif new_value == old_value:
			return f"{new_value}"
		else:
			result = float(old_value) - float(new_value)
			return f"{new_value} \u2193"

	def compare_dump(self):
		with open(f'{self.direct}log.json', 'r') as old_dump:
			old_dict = json.load(old_dump)
			for key ,val in self.DICT_VALUES.items():
				if key not in old_dict:
					return False
				else:
					if val not in old_dict.values():
						return True
			return False
				


class PushNotify:
	def __init__(self):
		self.bot = telebot.TeleBot(settings.BOT)
		self.msg = f"Курс на {datetime.datetime.today().strftime('%d.%m (%H:%M)')}:\n" 
		self.msg += f"```\n{'Покупка:':^5}{'Продажа:':^37}\n"

	def message_prepare(self, new_update, sale):
		self.msg += f"{new_update:22}{sale:22}\n"

	def send_notify(self, text):
		self.bot.send_message(settings.CHANNEL, f"{text}```", parse_mode='Markdown')

	def sticker_id(self):
		self.bot.send_sticker(settings.CHANNEL, settings.STICKER)


class Applicaion:
	def __init__(self):
		self.page = PageActions()
		self.datepage = DataPrepare()
		self.notify = PushNotify()

	def run(self):
		self.page.get_page()
		self.datepage.grep_values()
		if self.datepage.compare_dump():
			self.notify.send_notify(self.datepage.compare_purchase())
			self.page.log_write(self.datepage.DICT_VALUES)
		else:
			sys.exit()


if __name__ == '__main__':
	app = Applicaion()
	app.run()

