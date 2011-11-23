#!/usr/bin/python2

############################################
##
##  Charry 0.9 (Python rewrite)
##  A Twitter client written in Python
##
##  Copyright (c) 2011 soren121.
##
############################################

import gtk
import sys
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
		# Add tweets organizer to scrolling view
		tweetscroll.add_with_viewport(self.tweets)
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

	def loadtweets(self):
		class listener(tweepy.StreamListener):
			def on_status(self, status):
				try:
					print status.author.screen_name + status.text
				except Exception, e:
					print >> sys.stderr, 'Encoutnered Exception:', e
					pass
			
			def on_error(self, status_code):
				print >> sys.stderr, 'Encountered Exception:', status_code
				return True
			
			def on_timeout(self):
				print >> sys.stderr, 'Timeout...'
				return True
		streaming = tweepy.streaming.Stream(self.auth, listener(), timeout = 60)
		return False
	
	def gtkPrompt(self, name):
		prompt = gtk.MessageDialog(None, 0, gtk.MESSAGE_QUESTION, gtk.BUTTONS_OK_CANCEL, name)
		prompt.set_title("Prompt")
		entry = gtk.Entry()
		prompt.vbox.add(entry)
		prompt.show_all()
		if prompt.run() == gtk.RESPONSE_CANCEL:
			rval = False
		else:
			rval = entry.get_text()
		prompt.destroy()
		return rval
		
	def load(self):
		# Check if we've done OAuth login already
		if self.settings.find("oauth/accessToken") is None:
			print "no access token!"
			gtk.idle_add(self.oauth)
		else:
			print "access token found!"
			# Connect to the Twitter API
			consumerToken = self.settings.find("oauth/consumerToken")
			consumerSecret = self.settings.find("oauth/consumerSecret")
			accessToken = self.settings.find("oauth/accessToken")
			accessSecret = self.settings.find("oauth/accessSecret")
			self.auth = tweepy.OAuthHandler(consumerToken.text, consumerSecret.text)
			self.auth.set_access_token(accessToken, accessSecret)
			self.api = tweepy.API(self.auth)
			# Load tweets
			gtk.idle_add(self.loadtweets)

# Initialize and load Charry		
charry = Charry()
charry.load()
# Begin main GUI loop
gtk.main()
