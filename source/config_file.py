import pandas as pd
import copy


class Config:
    def __init__(self, config_path):
        self.path = config_path
        self.config_keys = {}
        self.config_values = {}
        self.full_dictionary = {}

    def get_config(self, response):
        try:
            read_wb = pd.ExcelFile(self.path)
            for sheet in read_wb.sheet_names:
                self.full_dictionary[sheet] = {}
                with pd.ExcelFile(self.path) as reader:
                    df = pd.read_excel(reader, sheet, keep_default_na=False, na_filter=False)
                    df.columns = [col.strip().lower() for col in list(df.columns)]
                    if "name" in df:
                        self.config_keys[sheet] = [str(k).strip() for k in df['name'].tolist() if str(k).strip() != '']
                        self.full_dictionary[sheet]['keys'] = df['name'].tolist()
                    else:
                        response.config_wrongs['without_name_col'].append(sheet)
                    if "value" in df:
                        self.config_values[sheet] = [str(k).strip() for k in df['value'].tolist() if
                                                     str(k).strip() != '']
                        self.full_dictionary[sheet]['values'] = df['value'].tolist()
                    else:
                        response.config_wrongs['without_value_col'].append(sheet)

            if len(self.config_keys.keys()) == 0:
                response.config_wrongs['empty'] = True
                raise Exception('*')
        except Exception as e:
            if len(e.args) > 0 and e.args[0] == ('*'):
                raise Exception
            response.config_wrongs['cant_open'] = True
            raise e

    def __check_unused_configs(self, all_xaml_responses, response):
        unused_keys = copy.deepcopy(self.config_keys)
        for xaml_respose in all_xaml_responses:
            for first_key in xaml_respose['used_config'].keys():
                if first_key in unused_keys.keys():
                    for second_key in xaml_respose['used_config'][first_key]:
                        if second_key in unused_keys[first_key] or second_key.strip() == '':
                            unused_keys[first_key].remove(second_key)
        response.unused_keys_config = unused_keys

    @staticmethod
    def update_val(value):
        value = str(value)
        value = value.strip().replace('\n', '\\n')
        if len(value) > 50:
            value = value[:50] + '...'
        return value

    def __check_untrim_configs(self, response):
        for sheet in self.full_dictionary:
            without_trim_sheet = {'keys': [], 'values': []}
            if 'keys' in self.full_dictionary[sheet].keys():
                for key in self.full_dictionary[sheet]['keys']:
                    if str(key).strip() != str(key) and str(key).strip() != '':
                        without_trim_sheet['keys'].append(self.update_val(key))

            if 'values' in self.full_dictionary[sheet].keys():
                for val in self.full_dictionary[sheet]['values']:
                    if str(val).strip() != str(val) and str(val).strip() != '':
                        without_trim_sheet['values'].append(self.update_val(val))

            if len(without_trim_sheet['keys']) > 0 or len(without_trim_sheet['values']) > 0:
                response.config_wrongs['without_trim'][sheet] = without_trim_sheet

    def check_config_file(self, all_xaml_responses, response):
        self.__check_unused_configs(all_xaml_responses, response)
        self.__check_untrim_configs(response)
