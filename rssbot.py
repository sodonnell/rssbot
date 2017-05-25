#!/usr/bin/env python
"""rssbot.py

	This is the Python version of the Automated RSS Feed "Engine" 
	used to collect data for the rssbot.org project, which was running 
	from 2004-2016, and is no longer an active project or domain/service. 

	The library used for mysql is probably outdated by now, as I haven't 
	used python w/ mysql for quite some time, but perhaps it still works.

	I had some issues with the older version of python when processing unicode 
	data, but that should be resolved in python >= v2.7.

	This script has not been modified since 2010, and hasn't been executed since 2012, 
	so I'm releasing it to the public, for what it's worth, or not worth.
	
	Initial Configuration on Ubuntu Linux:

		 sudo apt-get install python-mysqldb python-feedparser

	$Id: rssbot.py,v 1.5 2010/09/13 22:31:58 seanodonnell Exp $

"""

__version__ = "3.0"
__author__ = "Sean O'Donnell <sean@seanodonnell.com>"

__license__ = "GPL"
__copyright__ = "Copyright 2009, seanodonnell.com"


import MySQLdb, feedparser, sys
#import threading

#sys.setdefaultencoding('utf-8') 

class PyRSSbot:
	def __init__(self):
		# SET DEFAULT OBJECT PARAMS
		self.title = "PyRSSbot"
		self.set_root_url("http://www.rssbot.org/")
		self.set_useragent("PyRSSbot/1.0 +%s" % self.root_url)
		self.set_max_feeds(250)
		self.db_connect()
		self.get_feeds()
		self.debug = 1
		
	def set_root_url(self,url):
		# define the root URL for the rssbot.org webUI
		self.root_url = url

	def set_max_feeds(self,int):
		# Maximum number of RSS Feeds to scour per-session (250 max suggested)
		self.maxfeeds = int

	def set_useragent(self,agent):
		# define a custom user agent for this application
		self.user_agent = agent
		feedparser.USER_AGENT = agent
		
	def db_connect(self):
		self.conn = MySQLdb.connect (host = "localhost", user = "rssbot", passwd = "l3gacy_b0t", db = "rssbot")
		#return self.conn

	def get_feeds(self):
		sql = "SELECT title, link, id FROM tbl_rss_feeds WHERE active = 'Y' ORDER BY RAND() LIMIT 0, %s "
		cursor = self.conn.cursor()
		cursor.execute(sql, self.maxfeeds)
		self.feeds = cursor.fetchall()
		self.feeds_count = cursor.rowcount
		cursor.close()

	def deactivate_feed(self,id):
		cursor = self.conn.cursor()
		cursor.execute("UPDATE tbl_rss_feeds SET active = 'N' WHERE id = %s",id)
		cursor.close()
		print("Feed %d de-activated.", id)
		
	def add_link(self,pid,title,link,pubdate=''):
		title = title.encode('utf-8')
		title = title.replace("'","\'")
		title = title.replace('"','\"')
		link = link.encode('utf-8')
		cursor = self.conn.cursor()
		if pubdate:
			sql = "INSERT IGNORE INTO tbl_rss_archive ( pid, title, link, feed_id, pubdate ) VALUES (%s,%s,%s,%s,%s)"
			cursor.execute(sql, (pid,title,link,pid,pubdate))
		else:
			sql = "INSERT IGNORE INTO tbl_rss_archive ( pid, title, link, feed_id) VALUES (%s,%s,%s,%s)"
			cursor.execute(sql, (pid,title,link,pid))

		self.conn.commit()
		id = cursor.lastrowid
		cursor.close()
		return id

        def add_link_if_not_exists(self,pid,title,link,pubdate=''):
                title = title.encode('utf-8')
                title = title.replace("'","\'")
                title = title.replace('"','\"')
                link = link.encode('utf-8')
                cursor = self.conn.cursor()
		sql = "SELECT count(id) AS existing_id FROM tbl_rss_archive WHERE link = '%s'"
		cursor.execute(sql,link)
		self.existing_link = cursor.fetchall()
		cursor.close()

		if self.existing_link.existing_id < 1:
			cursor = self.conn.cursor()

                	if pubdate:
                	        sql = "INSERT IGNORE INTO tbl_rss_archive ( pid, title, link, feed_id, pubdate ) VALUES (%s,%s,%s,%s,%s)"
                	        cursor.execute(sql, (pid,title,link,pid,pubdate))
                	else:
                	        sql = "INSERT IGNORE INTO tbl_rss_archive ( pid, title, link, feed_id, pubdate) VALUES (%s,%s,%s,%s,NOW())"
                	        cursor.execute(sql, (pid,title,link,pid))
                                
                	self.conn.commit()
                	id = cursor.lastrowid
                	cursor.close()
                	return id
		else:
			return 0

i=0
j=0
k=0

rssbot = PyRSSbot()

print "\n"+ rssbot.user_agent

if rssbot.feeds_count > 0:

	print "Aggregating %d Feeds\n" % rssbot.feeds_count

	for feed in rssbot.feeds:
	
		#if rssbot.debug:
		#	print "\n-----\n\nParsing Feed: %s, %s" % (feed[0], feed[1])
	
		rss = feedparser.parse(feed[1],referrer=rssbot.root_url)
	
		if rss.feed.has_key('title'):
	
			if rssbot.debug:
				print "RSS Feed Title: %s" % rss.feed.title.encode('utf-8')
	
			if len(rss.entries) > 0:
				for entry in rss.entries:
					if entry.has_key('title') and entry.has_key('link'):
	
						if 'pubDate' in entry:
							id = rssbot.add_link_if_not_exists(feed[2],entry.title,entry.link,entry.pubDate)
						else:
							id = rssbot.add_link_if_not_exists(feed[2],entry.title,entry.link)

						try:
							if id > 0:
								if rssbot.debug:
									print("\nAdded Record (ID): %d") % id
									print("\t"+ str(entry.title))
									print("\t"+ str(entry.link))
								k=k+1
						except:
							print("Exception thrown while processing item.")

						j=j+1
		else:
			rssbot.deactivate_feed(feed[2])
			
		i=i+1

rssbot.conn.close()

print "\n-----\n\nProcessed %d feeds, %d items, and added %d new links to the database." % (i,j,k)