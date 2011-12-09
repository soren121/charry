#!/usr/bin/env python

############################################
##
##  Charry 0.9 (Python rewrite)
##  A Twitter client written in Python
##
##  Copyright (c) 2011 soren121.
##
############################################

import threading, thread, gtk, tweepy, re, webbrowser
from xml.etree.ElementTree import ElementTree, Element, SubElement
from urllib import urlretrieve
from dateutil.parser import parse
from dateutil.tz import tzlocal
from xml.sax.saxutils import escape
gtk.gdk.threads_init()
	
class Charry():
	def __init__(self):
		# Create window
		self.window = gtk.Window()
		# Set title, size, and action for close button
		self.window.set_title("Charry")
		self.window.set_size_request(430, 600)
		self.window.connect("destroy", self.quit)
		
		# Open settings XML
		self.settings = ElementTree()
		self.settings.parse("settings.xml")

		# Start vertical organizer
		vbox = gtk.VBox()
		self.window.add(vbox)

		# Start menubar
		mb = gtk.MenuBar()
		# Add menubar to vertical organizer
		vbox.pack_start(mb, False, False)

		# Make Charry and Options menu items
		mlcharry = gtk.MenuItem("Charry")
		mloptions = gtk.MenuItem("Options")
		# Append menu items to menubar
		mb.append(mlcharry)
		mb.append(mloptions)

		# Make the menus to go along with those
		mcharry = gtk.Menu()
		moptions = gtk.Menu()
		# And connect the menus to their top-level items
		mlcharry.set_submenu(mcharry)
		mloptions.set_submenu(moptions)

		# Make Exit item for Charry menu
		miexit = gtk.MenuItem("Exit")
		# Connect item to exit action
		miexit.connect("activate", self.quit)
		# Add to Charry menu
		mcharry.append(miexit)

		# Create new vertical pane split
		vpane = gtk.VPaned()
		vpane.set_border_width(3)
		vpane.set_position(480)
		# Add to vertical organizer
		vbox.pack_start(vpane)	

		# Create notebook (tabbed thingy)
		self.tabs = gtk.Notebook()
		self.tabs.set_tab_pos(gtk.POS_LEFT)
		# Add notebook to vertical pane split
		vpane.add1(self.tabs)

		# Create tab page one (timeline)
		timeline = gtk.Label("Timeline")
		timeline.set_angle(90)
		# Create scrolling view
		tweetscroll = gtk.ScrolledWindow()
		tweetscroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		# Create new vertical organizer for tweets
		self.tweets = gtk.VBox(False, 10)
		# Change color of the page to white
		tweetview = gtk.Viewport()
		color = tweetview.get_style()
		tweetview.modify_bg(gtk.STATE_NORMAL, color.white)
		# Add vertical organizer to scrolling window and viewport
		tweetview.add(self.tweets)
		tweetscroll.add(tweetview)
		# Add this tab page to the notebook
		self.tabs.append_page(tweetscroll, timeline)
		
		# Create tab page two (search)
		search = gtk.Label("Search")
		search.set_angle(90)
		# Create organizers
		search_vbox = gtk.VBox()
		search_hbox = gtk.HBox()
		# Create widgets
		search_text = gtk.Label("Search terms: ")
		self.search_entry = gtk.Entry()
		search_button = gtk.Button(stock = gtk.STOCK_OK)
		# Link widgets to signals
		self.search_entry.connect("activate", self.on_enter, search_button)
		search_button.connect("clicked", self.searchTweets, self.search_entry)
		# Pack widgets into horizontal organizer
		search_hbox.pack_start(search_text, False, False)
		search_hbox.pack_start(self.search_entry, True, True)
		search_hbox.pack_start(search_button, False, False)
		# Create scrolled window for tweets
		search_scroll = gtk.ScrolledWindow()
		search_scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		# Create vertical organizer for tweets
		self.search = gtk.VBox(False, 10)
		# Change color of the page to white
		searchview = gtk.Viewport()
		color = searchview.get_style()
		searchview.modify_bg(gtk.STATE_NORMAL, color.white)
		# Add tweet vertical organizer to scrolling window and viewport
		searchview.add(self.search)
		search_scroll.add(searchview)
		# Add scrolled window to search vbox
		search_vbox.pack_start(search_hbox, False, False)
		search_vbox.pack_start(search_scroll, True, True)
		# Add tab page to Notebook
		self.tabs.append_page(search_vbox, search)

		# Create tweet submission box
		sbox_vbox = gtk.VBox(False, 5)
		self.sbox_hbox = gtk.HBox(False, 5)
		self.sbox = gtk.TextView()
		self.sboxb = gtk.TextBuffer()
		self.sbox.set_buffer(self.sboxb)
		self.sbox.set_wrap_mode(gtk.WRAP_WORD_CHAR)
		self.sbox.connect("key-press-event", self.tweetSubmit)
		sbox_vbox.pack_end(self.sbox, True, True)
		sbox_count = gtk.Label(140 - int(self.sboxb.get_char_count()))
		sbox_count.set_justify(gtk.JUSTIFY_RIGHT)
		self.sboxb.connect("changed", self.update_char_count, sbox_count)
		self.sbox_hbox.pack_end(sbox_count, False, False)
		sbox_vbox.pack_start(self.sbox_hbox, False, False)
		vpane.add2(sbox_vbox)

		# Create statusbar
		statusbar = gtk.Statusbar()
		eventbox = gtk.EventBox()
		eventbox.add(statusbar)
		vbox.pack_start(eventbox, False, False)

		# Focus tweet submission box
		self.sbox.grab_focus()

		# Show all widgets
		self.window.show_all()

	def oauth(self):
		# Pull the consumer token and token secret out of the XML
		consumerToken = self.settings.find("oauth/consumerToken")
		consumerSecret = self.settings.find("oauth/consumerSecret")
		# Connect to the Twitter API without access tokens (because we don't have any yet)
		auth = tweepy.OAuthHandler(consumerToken.text, consumerSecret.text)
		# Try to get the authorization URL we need to get the verifier token
		try:
			redirect = auth.get_authorization_url()
		except tweepy.TweepError:
			print "Error! Failed to get request token."
		# Open a web browser to show the user the verifier token
		webbrowser.open(redirect, 2, True)
		# Ask the user for the verifier token
		verifier = self.gtkPrompt("Enter PIN: ")
		# Give Twitter its verifier token back in exchange for access tokens
		try:
			auth.get_access_token(verifier)
		except tweepy.TweepError:
			print "Error! Failed to get access token."
		# Plug the access tokens in and verify that everything's correct
		auth.set_access_token(auth.access_token.key, auth.access_token.secret)
		self.api = tweepy.API(auth)
		if self.api.verify_credentials():
			# Save access tokens to XML
			xml_oauth = self.settings.find("oauth")
			xml_accessToken = SubElement(xml_oauth, "accessToken")
			xml_accessToken.text = auth.access_token.key
			xml_accessSecret = SubElement(xml_oauth, "accessSecret")
			xml_accessSecret.text = auth.access_token.secret
			self.settings.write("settings.xml")
			# Restart
			import sys, os
			python = sys.executable
			os.execl(python, python, *sys.argv)
		else:
			print "Error! OAuth credentials are incorrect."
		return False
		
	def link_handler(self, label, uri):
		# Is this link a hashtag?
		if uri[0:4] == "C:HT":
			# It is!
			# Open the search tab
			self.tabs.set_current_page(1)
			# Set the search entry box to the hashtag in the link
			self.search_entry.set_text(uri[4:])
			# Start a search with that hashtag
			self.searchTweets(None, self.search_entry)
			
	def cancel_reply(self, button, label):
		# Destroy the "in reply to" label and its cancel button
		label.destroy()
		button.destroy()
		# Empty out tweet box
		self.sboxb.set_text("")
		# Clear the reply ID
		self.tweet_id = None
			
	def reply(self, button, tweet_id, name):
		# Create "in reply to" label above the tweet box
		label = gtk.Label(name)
		label.set_markup("in reply to <b>" + name + "</b>")
		self.sbox_hbox.pack_start(label, False, False)
		
		# Make a cancel reply button to go along with it
		cancel = gtk.Button("X", gtk.STOCK_CANCEL)
		cancel.connect("clicked", self.cancel_reply, label)
		self.sbox_hbox.pack_start(cancel, False, False)
		
		# Add "@USERNAME" to the tweet box
		self.sboxb.set_text("@" + name + " ")
		# Set the ID of the tweet we're replying to
		self.tweet_id = tweet_id
		
		# Show those widgets we just made
		label.show()
		cancel.show()
		
		# Focus the tweet box
		self.sbox.grab_focus()
		
	def retweet(self, button, tweet_id):
		# Well, isn't this short and sweet? Retweet it!
		self.api.retweet(tweet_id)
		
	def tweetFormat(self, tweet, type = "normal"):
		# Search compatibility
		if type is "search":
			screen_name = tweet.from_user
			profile_image_url = tweet.profile_image_url
			tweets = self.search
		else:
			screen_name = tweet.user.screen_name
			profile_image_url = tweet.user.profile_image_url
			tweets = self.tweets
	
		# Check to see if we've cached that user's avatar already
		import os
		if not os.path.exists("cache/images/" + screen_name + ".cache"):
			# Retrieve avatar and save to cache/images/USERNAME.cache
			urlretrieve(profile_image_url, "cache/images/" + screen_name + ".cache")
		# Load avatar into GDK pixbuf at size 48x48
		avatar_pb = gtk.gdk.pixbuf_new_from_file_at_size("cache/images/" + screen_name + ".cache", 48, 48)
		# Make GTK image widget from GDK pixbuf
		avatar = gtk.image_new_from_pixbuf(avatar_pb)
		
		# Create horizontal organizer to fit username and buttons
		hbox = gtk.HBox(False, 5)
		
		# Create Label for username
		name = gtk.Label()
		name.set_markup("<b>" + screen_name + "</b>")
		hbox.pack_start(name, False, False)
		
		# Create reply button
		reply = gtk.Button("Reply")
		reply.connect("clicked", self.reply, tweet.id, screen_name)
		hbox.pack_start(reply, False, False)
		
		# Create retweet button
		retweet = gtk.Button("Retweet")
		retweet.connect("clicked", self.retweet, tweet.id)
		hbox.pack_start(retweet, False, False)
		
		# Use regexes to link URLs, hashtags, and usernames
		urlregex = re.compile("(http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)", re.IGNORECASE)
		linked = escape(tweet.text)
		linked = urlregex.sub(r'<a href="\1">\1</a>', linked)
		linked = re.sub(r'(\A|\s)@(\w+)', r'\1<a href="http://www.twitter.com/\2">@\2</a>', linked)
		linked = re.sub(r'(\A|\s)#(\w+)', r'\1<a href="C:HT#\2">#\2</a>', linked)
		
		# Create Label for tweet text
		text = gtk.Label()
		text.set_alignment(0, 0)
		text.set_selectable(True)
		text.set_justify(gtk.JUSTIFY_LEFT)
		text.set_line_wrap(True)
		text.set_size_request(300, -1)
		text.set_markup(linked)
		# Connect links to our custom link handler
		text.connect("activate-link", self.link_handler)
		
		# Create Label for date/time
		timedate = gtk.Label()
		timedate.set_alignment(0, 0)
		timedate.set_selectable(True)
		timedate_str = parse(str(tweet.created_at) + " +0000").astimezone(tzlocal()).strftime("X%I:%M %p on %A, %b X%d").replace("X0", "").replace("X", "")
		timedate.set_markup("<small>" + timedate_str + "</small>")

		# Organize our elements
		tweetbox = gtk.HBox()
		tweetbox_inner = gtk.VBox()
		tweetbox.pack_end(tweetbox_inner)
		tweetbox.set_size_request(370, -1)
		tweetbox.pack_start(avatar)
		tweetbox_inner.pack_start(hbox, False, False)
		tweetbox_inner.pack_start(text, False, False)
		tweetbox_inner.pack_start(timedate, False, False)
		
		# Add tweet to tweets vertical organizer
		tweets.pack_start(tweetbox, padding = 3)
		# If this tweet is streaming, let's put it at the top, because we know it's the newest
		if type is "streaming":
			tweets.reorder_child(tweetbox, 0)
		# Show tweet
		tweets.show_all()
		
		return tweet
		
	class tweetListener(tweepy.streaming.StreamListener):
		def __init__(self, tweetFormat):
			tweepy.streaming.StreamListener.__init__(self)
			self.tweetFormat = tweetFormat
		def on_status(self, tweet):
			try:
				val = self.tweetFormat(tweet, "streaming")
				print val
			except:
				pass
			return True		
		
	def streamTweets(self, auth):
		# Display 20 tweets from the user's timeline
		for tweet in self.api.home_timeline():
			# Use tweetFormat() to format tweet nicely
			self.tweetFormat(tweet)
		# Initialize stream
		self.stream = tweepy.streaming.Stream(auth = auth, listener = self.tweetListener(self.tweetFormat), timeout = 60)
		# Start streaming from the user's timeline (in another thread, so we don't lock up the GUI)
		self.stream.userstream(async = True)
		# Update UI so it doesn't remain frozen
		while gtk.events_pending():
			gtk.main_iteration()
		return
		
	def searchTweets(self, button, entry):
		q = entry.get_text()
		# Clear search container
		for tweet in self.search.get_children():
			tweet.destroy()
		# Is the query empty?
		if q is not "":
			# List search results, run through tweet formatter
			for tweet in self.api.search(q):
				self.tweetFormat(tweet, "search")
		
	def tweetSubmit(self, widget, event):
		# Check if the user pressed Enter/Return
		if event.keyval == gtk.gdk.keyval_from_name('Return'):
			# Check if the user pressed Enter AND Shift (because that's a new line)
			if not (event.state and gtk.gdk.SHIFT_MASK):
				# Get the tweet text
				tweet = self.sboxb.get_text(self.sboxb.get_start_iter(), self.sboxb.get_end_iter())
				# Make sure the length is good
				if len(tweet) > 0 and len(tweet) <= 140:
					# Are we replying?
					if self.tweet_id != None:
						# Yeah, send Twitter the ID of the tweet we're replying to
						self.api.update_status(tweet, self.tweet_id)
					else:
						# Not a reply, just send the tweet
						self.api.update_status(tweet)
					# Empty out the tweet box
					self.sboxb.set_text('')
					return True
			else:
				# Ignore action
				return False
		else:
			# Ignore action
			return False

	def gtkPrompt(self, name):
		# Create new GTK dialog with all the fixings
		prompt = gtk.MessageDialog(None, 0, gtk.MESSAGE_QUESTION, gtk.BUTTONS_OK_CANCEL, name)
		# Set title of dialog
		prompt.set_title("Prompt")
		# Create and add entry box to dialog
		entry = gtk.Entry()
		#entry.connect("activate", self.on_enter, prompt.action_area.get_children()[1])
		prompt.vbox.add(entry)
		# Show all widgets in prompt
		prompt.show_all()
		# Run dialog until user clicks OK or Cancel
		if prompt.run() == gtk.RESPONSE_CANCEL:
			# User cancelled dialog
			rval = False
		else:
			# User clicked OK, grab text from entry box
			rval = entry.get_text()
		# Destory prompt
		prompt.destroy()
		# Give the good (or bad) news
		return rval
		
	def on_enter(self, entry, button):
		button.clicked()
		
	def update_char_count(self, sboxb, sbox_count):
		# If the user tries to type more than 140 characters, delete anything in the range of 140-end of buffer
		if (140 - sboxb.get_char_count()) < 0 :
			sboxb.delete(sboxb.get_iter_at_offset(140), sboxb.get_end_iter())
		# Set character count to 0 in bold
		if (140 - sboxb.get_char_count()) <= 0 :
			sbox_count.set_markup('<span foreground="#BF1313"><b>0</b></span>')
		# If less than 20, set character count to the color red
		elif (140 - sboxb.get_char_count()) < 20:
			sbox_count.set_markup('<span foreground="#BF1313">' + str(140 - sboxb.get_char_count()) + '</span>')
		# Show character count normally if more than 20
		else:
			sbox_count.set_markup(str(140 - sboxb.get_char_count()))
		
	def load(self):
		# Check if we've done OAuth login already
		if self.settings.find("oauth/accessToken") is None:
			print "no access token!"
			# We don't have access tokens, let's ask Twitter for them
			gtk.idle_add(self.oauth)
		else:
			print "access token found!"
			# Connect to the Twitter API
			consumerToken = self.settings.find("oauth/consumerToken")
			consumerSecret = self.settings.find("oauth/consumerSecret")
			accessToken = self.settings.find("oauth/accessToken")
			accessSecret = self.settings.find("oauth/accessSecret")
			auth = tweepy.OAuthHandler(consumerToken.text, consumerSecret.text)
			auth.set_access_token(accessToken.text, accessSecret.text)
			self.api = tweepy.API(auth)
			# Check tokens
			if self.api.verify_credentials():
				# Load tweets
				self.streamTweets(auth)
		return

	def quit(self, object):
		self.stream.disconnect()
		gtk.main_quit()

# Initialize and load Charry
charry = Charry()
charry.load()

# Begin main GUI loop
gtk.main()
