############################################
##
##  Charry 0.9 (Python rewrite)
##  A Twitter client written in Python
##
##  Copyright (c) 2011 soren121.
##
############################################

import gtk

class Charry(gtk.Window):
	def __init__(self):
		super(Charry, self).__init__()
	
		# Set title, size, and action for close button
		self.set_title("Charry")
		self.set_size_request(430, 600)
		self.connect("destroy", gtk.main_quit)
	
		# Start vertical organizer
		vbox = gtk.VBox()
		self.add(vbox)
	
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
		tweets = gtk.VBox(False, 10)
		# Add tweets organizer to scrolling view
		tweetscroll.add_with_viewport(tweets)
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
		self.show_all()

# Run class and start GUI loop
Charry()
gtk.main()