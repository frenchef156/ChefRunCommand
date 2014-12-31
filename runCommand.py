import sublime, sublime_plugin, subprocess, json
from os.path import dirname, realpath


class ChefRunCommand(sublime_plugin.TextCommand):

	curView = None
	initialRegion = None
	inputPanelView = None

	pluginFilename = dirname(realpath(__file__)) + "/" + "command_history"

	KEY_HISTORY = 'history'

	HISTORY_MAX_SIZE = 100

	historyIndex = -1

	selfChangeExpected = False

	def execute(self, command):
		print "chef called with: " + command
		#curView = sublime.active_window().active_view()
		#sel = self.curView.sel()
		region = self.initialRegion
		if region.empty():
			region = self.curView.line(region)
		regionText = self.curView.substr(region)
		print "got regionText: " + regionText
		p = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
		p.stdin.write(regionText)
		p.stdin.close()
		ret = p.stdout.read()
		print ret
		jmap = None
		with open(self.pluginFilename, 'r') as historyFile:
			jmap = json.load(historyFile)
			jhistory = jmap.get(self.KEY_HISTORY)
			if jhistory is not None and jhistory[len(jhistory)-1] != command:
				jhistory.append(command)
				if len(jhistory) > self.HISTORY_MAX_SIZE:
					jhistory = jhistory[1:]
					jmap[self.KEY_HISTORY] = jhistory
		if jmap is not None:
			with open(self.pluginFilename, 'w') as historyFile:
				json.dump(jmap, historyFile)
		edit = self.curView.begin_edit()
		self.curView.replace(edit, region, ret)
		self.curView.end_edit(edit)

	def run(self, edit):
		#self.view.insert(edit, 0, "Hello, World!")
		print "hello chef"
		self.curView = sublime.active_window().active_view()
		sel = self.curView.sel()
		print "sel: "; print sel[0]
		self.initialRegion = sublime.Region(sel[0].a, sel[0].b)
		self.historyIndex = -1 #meaning not showing history yet
		if len(sel) > 1:
			print "more then one selection, aborting"
			sublime.message_dialog("cannot run on more than ONE selection")
		else:
			self.inputPanelView = sublime.active_window().show_input_panel("chef| run command on input", "json_pp -f json", self.execute, self.onChange, None)

	# beware of change recurssion!!!
	def onChange(self, change):
		print "change: " + change
		if self.selfChangeExpected:
			print 'self change. do nothing.'
			self.selfChangeExpected = False
		else:
			if self.inputPanelView is not None and change.find('~~') != -1:
				with open(self.pluginFilename, 'r') as historyFile:
					jmap = json.load(historyFile)
					jhistory = jmap.get(self.KEY_HISTORY)
					if jhistory is not None:
						if self.historyIndex == -1:
							self.historyIndex = len(jhistory)-1
							replaceCommand = jhistory[self.historyIndex]
						elif self.historyIndex > 0:
							self.historyIndex -= 1
							replaceCommand = jhistory[self.historyIndex]
						else: # == 0
							self.historyIndex -= 1
							replaceCommand = ''
						self.selfChangeExpected = True
						edit = self.inputPanelView.begin_edit()
						self.inputPanelView.replace(edit, self.inputPanelView.visible_region(), replaceCommand)
						self.inputPanelView.end_edit(edit)
				