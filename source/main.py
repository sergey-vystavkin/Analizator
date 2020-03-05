import easygui
from os import path
import os
from source.response import Response
from source.config_file import Config
from source.xaml_file import Xaml
from multiprocessing import Pool

class Main:

    def __init__(self, path_to_main):
        self.unused_var_arg = {}
        self.no_exist_configs = {}
        self.already_checked = []
        self.path_to_main = path_to_main
        self.main_dir = path.dirname(path_to_main)
        self.path_to_config = None
        self.config_exist = False
        self.response = Response()
        self.config_obj = None
        self.used_xamls = []
        self.names = []

    def declare_config(self):
        if path.exists(path.join(self.main_dir, 'settings\\config.xlsx')):
            self.path_to_config = easygui.fileopenbox('Choose config if you have it',
                                                      default=path.join(self.main_dir, 'settings\\config.xlsx'))
        else:
            self.path_to_config = easygui.fileopenbox('Choose config if you have it', default=self.path_to_main)
        if self.path_to_config:
            self.config_exist = True
        return self.path_to_config

    def get_all_workflows(self, xaml_path=None):
        if not xaml_path:
            xaml_path = self.path_to_main
        try:
            xaml = Xaml(xaml_path, self.main_dir)
            self.used_xamls.append(xaml.path)
            for invoke_name in xaml.invokes.keys():
                invoke_path = path.join(self.main_dir, xaml.invokes[invoke_name]['workflow_path'])
                if invoke_path not in self.already_checked:
                    self.already_checked.append(invoke_path)
                    self.get_all_workflows(xaml_path=invoke_path)
        except Exception as e:
            if xaml_path == self.path_to_main:
                raise Exception(f"I can't open your main xaml!\n{str(e)}")
            self.response.wrong_invokes.append(f'{xaml_path}\n\t  ({str(e)})')

    def check_unused_xamls(self):
        used_xamls = [p.replace('/', '\\') for p in self.used_xamls]
        for r, d, f in os.walk(self.main_dir):
            for file in f:
                if os.path.splitext(file)[-1].lower() == '.xaml':
                    if os.path.join(r, file) not in used_xamls:
                        self.response.unused_xamls.append(os.path.join(r, file).replace(self.main_dir, ''))

    def check_current_xaml(self, xaml_path):
        xaml = Xaml(xaml_path, self.main_dir)
        xaml_response = {'name': xaml.name, 'used_config': {}, 'module_wrongs': {'vars': [], 'args': [],
                         'generic_values': [], 'hardcodes': [], 'duplicates': [], 'config_pairs': []}}
        xaml.check_xaml(xaml_response)
        if self.config_exist:
            xaml.check_xaml_config(common_config=self.config_obj.config_keys, response=xaml_response)
        return xaml_response

    def check_project(self):
        self.get_all_workflows()
        self.check_unused_xamls()
        with Pool(5) as p:
            all_xaml_responses = list(p.map(self.check_current_xaml, self.used_xamls))
        if self.config_exist:
            self.config_obj.check_config_file(all_xaml_responses, self.response)
            self.response.make_response(all_xaml_responses)
        else:
            self.response.make_response(all_xaml_responses)


def run():
    try:
        path_to_main = easygui.fileopenbox('Input full path to Main.xaml of your project')
        if path_to_main:
            main = Main(path_to_main)
            main.declare_config()
            if main.config_exist:
                main.config_obj = Config(main.path_to_config)
                try:
                    main.config_obj.get_config(main.response)
                except Exception:
                    main.config_exist = False

            main.check_project()
            main.response.show_for_user()
    except Exception as e:
        easygui.codebox('Something was wrong', 'Check exception', str(e))
