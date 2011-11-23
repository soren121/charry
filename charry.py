#!/usr/bin/env python

############################################
##
##  Charry 0.9 (Python rewrite)
##  A Twitter client written in Python
##
##  Copyright (c) 2011 soren121.
##
############################################

import gtk
import tweepy
from xml.etree.ElementTree import ElementTree, Element, SubElement

class Charry():
	def __init__(self):
		# Create window
		self.window = gtk.Window()
		# Set title, size, and action for close button
		self.window.set_title("Charry")
		self.window.set_size_request(430, 600)
		self.window.connect("destroy", gtk.main_quit)
		
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
		miexit.connect("activate", gtk.main_quit)
		# Add to Charry menu
		mcharry.append(miexit)

		# Create new vertical pane split
		vpane = gtk.VPaned()
		vpane.set_border_width(3)
		vpane.set_position(500)
		# Add to vertical organizer
		vbox.pack_start(vpane)	

		# Create notebook (tabbed thingy)
		tabs = gtk.Notebook()
		tabs.set_tab_pos(gtk.POS_LEFT)
		# Add notebook to vertical pane split
		vpane.add1(tabs)

		# Create tab page one
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
		tabs.append_page(tweetscroll, timeline)

		# Create tweet submission box
		sbox = gtk.TextView()
		sboxb = gtk.TextBuffer()
		sbox.set_buffer(sboxb)
		sbox.set_wrap_mode(gtk.WRAP_WORD)
		vpane.add2(sbox)

		# Create statusbar
		statusbar = gtk.Statusbar()
		eventbox = gtk.EventBox()
		eventbox.add(statusbar)
		vbox.pack_start(eventbox, False, False)

		# Focus tweet submission box
		sbox.grab_focus()

		# Show all widgets
		self.window.show_all()

	def oauth(self):
		# Import WebBrowser module
		import webbrowser
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
		api = tweepy.API(auth)
		if api.verify_credentials():
			# Save access tokens to XML
			xml_oauth = self.settings.find("oauth")
			xml_accessToken = SubElement(xml_oauth, "accessToken")
			xml_accessToken.text = auth.access_token.key
			xml_accessSecret = SubElement(xml_oauth, "accessSecret")
			xml_accessSecret.text = auth.access_token.secret
			self.settings.write("settings.xml")
			# Load tweets!
			self.loadtweets()
		else:
			print "Error! OAuth credentials are incorrect."
		return False
		
	def tweetFormat(self, tweet):
		# Get tweet vertical organizer
		tweets = self.tweets
		
		# Check to see if we've cached that user's avatar already
		import os, urllib
		if os.path.exists("cache/images/" + tweet.user.screen_name + ".cache") is not True:
			# Retrieve avatar and save to cache/images/USERNAME.cache
			urllib.urlretrieve(tweet.user.profile_image_url, "cache/images/" + tweet.user.screen_name + ".cache")
		# Load avatar into GDK pixbuf at size 48x48
		avatar_pb = gtk.gdk.pixbuf_new_from_file_at_size("cache/images/" + tweet.user.screen_name + ".cache", 48, 48)
		# Make GTK image widget from GDK pixbuf
		avatar = gtk.image_new_from_pixbuf(avatar_pb)
		
		# Create Label for username
		name = gtk.Label()
		name.set_alignment(0, 0)
		name.set_markup("<b>" + tweet.user.screen_name + "</b>")
		
		# Create TextView and disguise it as a label
		text = gtk.TextView()
		textbuffer = gtk.TextBuffer()
		text.set_buffer(textbuffer)
		text.set_editable(False)
		text.set_cursor_visible(False)
		text.set_wrap_mode(gtk.WRAP_WORD)
		text.set_size_request(300, -1)
		textbuffer.insert(textbuffer.get_end_iter(), tweet.text)
		
		# Organize our elements
		tweetbox = gtk.HBox()
		tweetbox_inner = gtk.VBox()
		tweetbox.pack_end(tweetbox_inner)
		tweetbox.set_size_request(370, -1)
		tweetbox.pack_start(avatar)
		tweetbox_inner.pack_start(name, False, False)
		tweetbox_inner.pack_start(text, False, False)
		
		# Add tweet to tweets vertical organizer
		tweets.pack_start(tweetbox)
		# Show tweet
		tweets.show_all()
		
		return

	def initialTweets(self, auth):
		# Load API
		api = tweepy.API(auth)
		# Display 20 tweets from the user's timeline
		for tweet in api.home_timeline():
			# Use tweetFormat() to format tweet nicely
			self.tweetFormat(tweet)
		# Tell GTK not to run this function this again
		# Streaming API will take over from here
		return False
		
	def streamTweets(self, auth):
		# Import streaming functions
		from tweepy.streaming import StreamListener, Stream
		# Tell Tweepy how we want to handle things on the stream
		class custom_listener(tweepy.StreamListener):
			def on_status(self, status):
				try:
					# For statuses, run them through the tweet formatter
					print tweet.text
				except:
					pass
				return
		# Initialize stream
		stream = tweepy.Stream(auth = auth, listener = custom_listener(), timeout = 60)
		# Start streaming from the user's timeline (in another thread, so we don't lock up the GUI)
		stream.sample()
		return
	
	def gtkPrompt(self, name):
		# Create new GTK dialog with all the fixings
		prompt = gtk.MessageDialog(None, 0, gtk.MESSAGE_QUESTION, gtk.BUTTONS_OK_CANCEL, name)
		# Set title of dialog
		prompt.set_title("Prompt")
		# Create and add entry box to dialog
		entry = gtk.Entry()
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
			api = tweepy.API(auth)
			# Check tokens
			if api.verify_credentials():
				# Load tweets
				gtk.idle_add(self.initialTweets, auth)
		# Return authentication handle so we can give it to streamTweets()
		return auth

# Initialize and load Charry
charry = Charry()
auth = charry.load()
#charry.streamTweets(auth)
# Begin main GUI loop
gtk.main()