import sublime, sublime_plugin, subprocess, json
from os.path import dirname, realpath


class ChefRunCommand(sublime_plugin.TextCommand):

	initialRegion = None
	inputPanelView = None

	pluginFilename = dirname(realpath(__file__)) + "/" + "command_history"

	KEY_HISTORY = 'history'

	HISTORY_MAX_SIZE = 100

	historyIndex = -1

	curCommand = None

	def execute(self, command, edit):
		print("chef called with: " + command)
		region = self.initialRegion
		if region.empty():
			region = self.view.line(region)
		regionText = self.view.substr(region)
		print("got regionText: " + regionText)
		p = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
		p.stdin.write(regionText.encode('utf-8'))
		p.stdin.close()
		ret = p.stdout.read().decode('utf-8')
		print(ret)
		jmap = None
		with open(self.pluginFilename, 'r') as historyFile:
			jmap = json.load(historyFile)
			jhistory = jmap.get(self.KEY_HISTORY)
			print("jhistory: ", jhistory)
			if jhistory is not None and (len(jhistory) < 1 or jhistory[len(jhistory)-1] != command):
				jhistory.append(command)
				if len(jhistory) > self.HISTORY_MAX_SIZE:
					jhistory = jhistory[1:]
					jmap[self.KEY_HISTORY] = jhistory
		if jmap is not None:
			with open(self.pluginFilename, 'w') as historyFile:
				json.dump(jmap, historyFile)
		# edit = self.view.begin_edit()
		self.view.replace(edit, region, ret)
		# self.view.end_edit(edit)

	def run(self, edit):
		print("hello chef")
		sel = self.view.sel()
		print("sel: ", sel[0])
		self.initialRegion = sublime.Region(sel[0].a, sel[0].b)
		self.historyIndex = -1 #meaning not showing history yet
		if len(sel) > 1:
			print("more then one selection, aborting")
			sublime.message_dialog("cannot run on more than ONE selection")
		else:
			if self.curCommand != None:
				self.execute(self.curCommand, edit)
				self.curCommand = None
			else:
				self.inputPanelView = self.view.window().show_input_panel("chef| run command on input", "json_pp -f json", self.setCommand, self.onChange, None)

	def setCommand(self, command):
		self.curCommand = command

	# beware of change recurssion!!!
	def onChange(self, change):
		print("change: " + change)
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
					self.inputPanelView = self.view.window().show_input_panel("chef| run command on input", replaceCommand, self.setCommand, self.onChange, None)
			