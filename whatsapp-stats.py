# -*- coding: utf-8 -*-
import sqlite3
import argparse
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from os.path import isfile
from time import time
from datetime import datetime, timedelta
import re
import numpy as np

class progress:
	def __init__(self, message_count):
		self.message_count = message_count
		self.process_count = 0
		self.time = time()
		self.second_count = 0
		self.messages_per_second = 0
		self.start_time = time()
	def new(self):
		self.process_count += 1
		self.second_count += 1
		if (time() - self.time > 1):
			self.messages_per_second = self.second_count
			self.second_count = 0
			self.time = time()
		print('Progress: {:.2f}% ({} messages per second)'.format(self.process_count*100/self.message_count, self.messages_per_second), end='\r')
	def exit(self):
		print('On average {:.2f} messages per second.\t\t'.format(self.message_count/(time()-self.start_time)))

def create_matrix(first_level, second_level):
	return [[0 for x in range(second_level)] for y in range(first_level)]
def create_array(size):
	return [0 for x in range(size)]
def filter(liste, filter_size):
	l = [0] * (len(liste) - filter_size + 1)
	for i in range(len(l)):
		l[i] = sum(liste[i:i+filter_size])/filter_size
	return l
def time_to_datetime(time):
	return datetime.fromtimestamp(int(time)/1000)
def get_popular_words(dic, count):
	result = {}
	for k,v in dic.items():
		if len(result) < count and v not in result:
			result[v] = k
		elif v in result:
			result[v] += ', ' + k
		elif v > min(result.keys()):
			del result[min(result.keys())]
			result[v] = k
	return sorted(result.items())
		

class data:
	counter = 0
	def __init__(self, size):
		self.m = create_matrix(3, size)
		self.c = create_matrix(3, size)
		self.filter_size = 0
		self.avg_chars = None
		self.stats = None
	def add(self, position, from_me, value):
		self.m[2][position] += 1
		self.m[from_me][position] += 1
		self.c[2][position] += value
		self.c[from_me][position] += value
	def smooth(self, filter_size):
		if self.avg_chars is None: self.__calc_avg()
		self.stats = self.total_stats()
		self.filter_size += filter_size - 1
		self.__calc_avg()
		for i in range(3):
			self.m[i] = filter(self.m[i], filter_size)
			self.avg_chars[i] = filter(self.avg_chars[i], filter_size)
	def plot(self, x_axis, xlabel='', ylabelm='Messages', ylabelc='Average message length', colors = 'r,g,b', save='', show=False, xrotation = 0, title = 'Whatsapp Chat Stats', linewidth = 1):
		plt.clf()
		x = np.linspace(x_axis[0], x_axis[1], num = len(self.m[2]))
		self.__plot(x, self.m, xlabel, ylabelm, colors, save, show, xrotation, title, linewidth)
		plt.clf()
		if self.avg_chars is None: self.__calc_avg()
		self.__plot(x, self.avg_chars, xlabel, ylabelc, colors, save, show, xrotation, title, linewidth)
	def plot_dates(self, startdate, enddate, xlabel='', ylabelm='Messages', ylabelc='Average message length', colors = 'r,g,b', save='', show=False, xrotation = 0, title = 'Whatsapp Chat Stats', linewidth = 1):
		plt.clf()
		x = mdates.drange(startdate, enddate - timedelta(days=self.filter_size), timedelta(days=1))
		plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
		plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=int(len(x)/11)))
		self.__plot(x, self.m, xlabel, ylabelm, colors, save, show, xrotation, title, linewidth)
		plt.clf()
		if self.avg_chars is None: self.__calc_avg()
		plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
		plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=int(len(x)/11)))
		self.__plot(x, self.avg_chars, xlabel, ylabelc, colors, save, show, xrotation, title, linewidth)
	def __plot(self, x, y, xlabel, ylabel, colors, save, show, xrotation, title, linewidth):
		colors = colors.split(',')
		plt.title(title)
		plt.plot(x, y[0], colors[0], linewidth=linewidth, label='you')
		plt.plot(x, y[1], colors[1], linewidth=linewidth, label='me')
		plt.plot(x, y[2], colors[2], linewidth=linewidth, label='total')
		plt.xlabel(xlabel)
		plt.ylabel(ylabel)
		plt.legend()
		plt.xticks(rotation=xrotation)
		plt.tight_layout()
		if len(save) == 0:
			save = 'whatsapp_stats{}.png'.format(data.counter)
			data.counter += 1
		plt.savefig(save, dpi=300)
		if show:
			plt.show()
	def __calc_avg(self):
		self.avg_chars = create_matrix(3, len(self.m[2]))
		for i in range(3):
			for j in range(len(self.m[2])):
				self.avg_chars[i][j] = self.c[i][j]/self.m[i][j] if self.m[i][j] != 0 else 0
	def total_stats(self):
		if self.stats is not None: return self.stats
		if self.avg_chars is None: self.__calc_avg()
		d = {}
		d['total_messages'] = [sum(self.m[0]), sum(self.m[1]), sum(self.m[2])]
		d['total_chars'] = [sum(self.c[0]), sum(self.c[1]), sum(self.c[2])]
		d['avg_chars'] = [sum(self.avg_chars[0])/len(self.avg_chars[0]), sum(self.avg_chars[1])/len(self.avg_chars[1]), sum(self.avg_chars[2])/len(self.avg_chars[2])]
		self.stats = d
		return d
		

if __name__ == '__main__':

# Parse command line arguments
	parser = argparse.ArgumentParser(description='Get whatsapp statistics')
	parser.add_argument('-pn', '--phone_numbers', metavar='phone_numbers', type=str, default="",
						help='Enter the international phone numbers of all chats you want to include in your statistics (comma separated)')
	parser.add_argument('filepath', help="Filepath to your 'msgstore.db'")
	#parser.add_argument('-v', '--verbose', action='count', help='verbose level, -v to -vvv')
	args = parser.parse_args()
	msg_db_path = args.filepath
	phone_numbers = []
	if len(args.phone_numbers) > 0:
		phone_numbers = [(''.join(i for i in s if i.isdigit())+ '@s.whatsapp.net') for s in args.phone_numbers.split(',')]  # Format phone numbers for SQL query
		
# Connect to database
	if not isfile(msg_db_path): print('File not found'); exit()
	co = sqlite3.connect(msg_db_path)
	cu = co.cursor()

# Get messages from database
	phone_query = ''
	if len(phone_numbers) > 0:
		phone_query = ' WHERE key_remote_jid = "' + '" OR "'.join(phone_numbers) + '"'
	# Get message count
	cu.execute('SELECT COUNT(*) FROM messages{}'.format(phone_query))
	message_count = cu.fetchone()[0]
	if message_count == 0:
		print('No messages found. Please try again with a diffente phone number')
		exit()
	else:
		print('Found {} messages'.format(message_count))
	# Get first and last date
	cu.execute('SELECT timestamp FROM messages{} LIMIT 1'.format(phone_query))
	start = time_to_datetime(cu.fetchone()[0])
	cu.execute('SELECT timestamp FROM messages{} ORDER BY timestamp DESC LIMIT 1'.format(phone_query))
	end = time_to_datetime(cu.fetchone()[0])
	day_diff = (end-start).days + 1
	# Get messages
	cu.execute('SELECT timestamp, key_from_me, data FROM messages{}'.format(phone_query))
	
# Setup counting vars
	day =  data(24 * 6)
	month = data(31)
	total = data(day_diff)
	words = {}
	
# Process messages
	p = progress(message_count)
	for row in cu:
		timestamp = time_to_datetime(row[0])
		from_me = int(row[1])
		text = row[2]
		if text is None: text = ""
		p.new()
		
		day.add(timestamp.hour * 6 + int(timestamp.minute / 10), from_me, len(text))
		month.add(timestamp.day - 1, from_me, len(text))
		total.add((timestamp.date() - start.date()).days - 1, from_me, len(text))
		for word in re.split(r'\n|\t|\r|\.|\?|\!|\s|\*|\[|\]|\(|\)|\{|\}|\"|\\|,', text):
			if len(word) > 0:
				w = word.lower()
				if w in words:
					words[w] += 1
				else:
					words[w] = 1
			
	p.exit()
	popular_words = get_popular_words(words, 100)

# Plot data
	day.smooth(4)
	day.plot([0, 23], xlabel='Hours per day')
	month.plot([1, 31], xlabel='Days per month')
	total.smooth(70)
	total.plot_dates(start, end, xrotation=45, linewidth=0.8)
	print(total.total_stats())
	
# Exit
	co.close()