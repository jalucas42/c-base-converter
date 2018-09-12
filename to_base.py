import sublime
import sublime_plugin

from . import convert
from . import config

class ToBaseCommand(sublime_plugin.TextCommand):
    def run(self, edit : sublime.Edit, base : int):
        if not config.settings():
            return

        for region in self.view.sel():
            s = self.view.substr(region)

            val = convert.to_base(s, base)

            if(val != None):
                self.view.replace(edit, region, val)

    def is_visible(self, base : int):
        if not config.settings() or not config.settings().get('context_menu_options_enabled', True):
            return False

        base_enabled = False
        for base_data in config.bases():
            if base_data['value'] == base:
                base_enabled = True
                break

        if not base_enabled:
            return False

        for region in self.view.sel():
            s = self.view.substr(region)

            if(convert.to_base(s, base) != None):
                return True

        return False

    def is_enabled(self):
        return config.settings() != None

class LoadStoredValuesCommand(sublime_plugin.TextCommand):
    def run(self, edit : sublime.Edit, values : list):
        regions = self.view.sel()

        # Ensure that current user selection is still the same as when
        if len(regions) != len(values):
            return

        # If user clicks away from quick_panel, it will lose focus but new selection will be empty
        # check for this case to avoid ambiguity
        if len(values) == 1 and regions[0].empty():
            return

        # Replace selection with initial values
        for s, region in zip(values, regions):
            self.view.replace(edit, region, s)

class ToBasePromptCommand(sublime_plugin.WindowCommand):
    first_opened = True
    last_used_index = 1

    stored_values = []

    def run(self):
        if not config.settings():
            return

        options = []

        for base_data in config.bases():
            options.append(base_data['string'])

        # Only option quick panel if any options are enabled
        if options:
            # Reset last_used_index if outside options list
            if self.last_used_index >= len(options):
                self.last_used_index = 0

            self.highlighted_index = self.last_used_index

            self.window.show_quick_panel(
                options, # Options list
                self.on_done, # On done handler
                0, # Flags (bitwise OR of sublime.MONOSPACE_FONT and sublime.KEEP_OPEN_ON_FOCUS_LOST)
                self.last_used_index, # Start index
                self.on_highlight # On highlight handler
            )

    def on_highlight(self, index : int):
        # Don't change value when quick panel is first opened
        if self.first_opened == True:
            self.first_opened = False

            # Store initial values
            self.stored_values = []
            if self.window.active_view():
                for region in self.window.active_view().sel():
                    self.stored_values.append(self.window.active_view().substr(region))

            return

        base = config.bases()[index]['value']

        if self.window.active_view():
            self.window.active_view().run_command("to_base", {"base": base})

    def on_done(self, index : int):
        self.first_opened = True

        if index == -1:
            if config.settings().get('revert_on_quick_panel_exit', True):
                # Load initial values
                self.window.active_view().run_command("load_stored_values", {"values": self.stored_values})
        else:
            base = config.bases()[index]['value']

            if self.window.active_view():
                self.window.active_view().run_command("to_base", {"base": base})

            self.last_used_index = index
