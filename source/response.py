import easygui
import os
import time


class Response:

    def __init__(self):
        self.text = ''
        self.config_wrongs = {'unused': {}, 'without_name_col': [], 'without_value_col': [], 'without_trim': {},
                              'cant_open': False, 'empty': False}
        self.unused_xamls = []
        self.wrong_invokes = []
        self.hardcode_part = ''
        self.config_part = ''
        self.module_part = ''
        self.invokes_part = ''
        self.unused_keys_config = {}

    def __make_hardcode_part(self, all_xaml_responses):
        idx = 1
        for xaml_respose in all_xaml_responses:
            if len(xaml_respose['module_wrongs']['hardcodes']) > 0:
                self.hardcode_part += f'  {idx}) {xaml_respose["name"]}\n'
                for hardcode in xaml_respose['module_wrongs']['hardcodes']:
                    self.hardcode_part += f'\t- {hardcode}\n'
                idx += 1

    def __make_config_part(self):
        if any(bool(k) for k in self.config_wrongs.keys()):
            if self.config_wrongs['cant_open']:
                self.config_part += f"  Catch error when try open your config, so I didn't check it :(\n"
                return

            if self.config_wrongs['empty']:
                self.config_part += f"  Can't find any values in config, so I didn't check it :(\n"
                return

            if len(self.config_wrongs['without_name_col']) > 0:
                self.config_part += f'  Sheets without "Name" column: {str.join(", ", self.config_wrongs["without_name_col"])}\n'

            if len(self.config_wrongs['without_value_col']) > 0:
                self.config_part += f'  Sheets without "Value" column: {str.join(", ", self.config_wrongs["without_value_col"])}\n'

        if len(self.unused_keys_config) > 0:
            if len(self.unused_keys_config.keys()) and any(len(val) > 0 for val in self.unused_keys_config.values()):
                self.config_part += f'  Unused keys:\n'
                for key in self.unused_keys_config.keys():
                    if len(self.unused_keys_config[key]) > 0:
                        self.config_part += f'\t- {key}: {str.join(", ", self.unused_keys_config[key])}\n'


        without_trim_part = ''
        for sheet in self.config_wrongs['without_trim'].keys():
            without_trim_part += f'\t- {sheet}:\n'
            if len(self.config_wrongs['without_trim'][sheet]['keys']) > 0:
                without_trim_part += f'\t\tkeys - {str.join(", ", self.config_wrongs["without_trim"][sheet]["keys"])}\n'
            if len(self.config_wrongs['without_trim'][sheet]['values']) > 0:
                without_trim_part += f'\t\tvalues - {str.join(", ", self.config_wrongs["without_trim"][sheet]["values"])}\n'

        if without_trim_part != '':
            self.config_part += f'  Has excess spaces around(need Trim):\n{without_trim_part}'


    def __make_module_part(self, all_xaml_responses):
        idx = 1
        for xaml_response in all_xaml_responses:
            xaml_part = ''

            if len(xaml_response['module_wrongs']["vars"]) > 0:
                xaml_part += f'\t- Unused variables: {str.join(", ", xaml_response["module_wrongs"]["vars"])}\n'

            if len(xaml_response['module_wrongs']["args"]) > 0:
                xaml_part += f'\t- Unused arguments: {str.join(", ", xaml_response["module_wrongs"]["args"])}\n'

            if len(xaml_response['module_wrongs']["config_pairs"]) > 0:
                xaml_part += f'\t- Config pair not exist: {str.join(", ", xaml_response["module_wrongs"]["config_pairs"])}\n'

            if len(xaml_response['module_wrongs']["generic_values"]) > 0:
                xaml_part += f'\t- Generic values: {str.join(", ", xaml_response["module_wrongs"]["generic_values"])}\n'

            if len(xaml_response['module_wrongs']["duplicates"]) > 0:
                xaml_part += f'\t- Duplicates display names: {str.join(", ", xaml_response["module_wrongs"]["duplicates"])}\n'

            if xaml_part != '':
                self.module_part += f'  {idx}) {xaml_response["name"]}\n' + xaml_part
                idx += 1

    def __make_invokes_part(self):
        if len(self.wrong_invokes) > 0:
            self.invokes_part += f"  I can't check this workflows, but they invoking in your project:\n"
            for invoke in self.wrong_invokes:
                self.invokes_part += f'\t- {invoke}\n'
        if len(self.unused_xamls) > 0:
            self.invokes_part += f"  This workflows are not used in project:\n"
            for invoke in self.unused_xamls:
                self.invokes_part += f'\t- {invoke}\n'



    def make_response(self, all_xaml_responses):
        self.__make_hardcode_part(all_xaml_responses)
        self.__make_module_part(all_xaml_responses)
        self.__make_config_part()
        self.__make_invokes_part()

        if any(s != '' for s in [self.hardcode_part, self.config_part, self.module_part, self.invokes_part]):
            self.text += f'Analisator success finish the work! Check result\n'
            if self.invokes_part:
                self.text += f"\n\nWORKFLOWS:\n\n"
                self.text += self.invokes_part

            if self.config_part:
                self.text += f'\n\nCONFIG\n\n'
                self.text += self.config_part

            if self.module_part:
                self.text += f'\n\nMODULS\n\n'
                self.text += self.module_part

            if self.hardcode_part:
                self.text += f'\n\nHARDCODES\n\n'
                self.text += self.hardcode_part

        else:
            self.text = f"Analisator success finish the work!\n I can't find any wrongs in your project, maybe it's perfect or empty :)"

    def show_for_user(self):
        report_file = f'Analizator report {time.strftime("%m%d%H%M%S")}.txt'
        try:
            with open(report_file, 'w') as data_file:
                data_file.write('\t*This file will be delete when you close window!*\n\n')
                data_file.write(self.text)
            os.system(f"notepad.exe {report_file}")
            os.remove(report_file)
        except:
            if os.path.exists(report_file):
                os.remove(report_file)
            easygui.codebox('Result', 'That is what I found', self.text)
