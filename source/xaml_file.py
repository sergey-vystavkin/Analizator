from bs4 import BeautifulSoup
import re

definition_attrs = ['currentindex', 'displayname']
definition_elements = ['assign.to', 'outargument', 'variable', 'x:property', 'ui:excelreadrange', 'ui:comment']


class Xaml:

    def __init__(self, xaml_path, main_dir):
        with open(xaml_path, "rb") as f:
            file_text = f.read()
        try:
            self.soup = BeautifulSoup(file_text, features='lxml')
        except Exception:
            self.soup = BeautifulSoup(file_text, features='html.parser')
        self.path = xaml_path
        self.name = xaml_path.replace(main_dir, '')[1:]
        self.variables = []
        self.arguments = {'in': [], 'out': [], 'in_out': []}
        self.invokes = {}
        self.unused_variables = []
        self.unused_arguments = []
        self.duplicates_names = []
        self.generic_values = []
        self.hardcodes = []
        self.module_configs = {}

        xaml_invokes = self.soup.find_all('ui:invokeworkflowfile')
        xaml_invokes.extend(self.soup.find_all('ui:invokeworkflowinteractive'))
        for invoke in xaml_invokes:
            self.invokes[invoke['displayname']] = {'in': [], 'out': [], 'in_out': [], 'workflow_path': ''}
            self.invokes[invoke['displayname']]['workflow_path'] = invoke['workflowfilename']
            for arg in invoke.find_all('outargument'):
                self.invokes[invoke['displayname']]['out'].append(arg['x:key'])
            for arg in invoke.find_all('inargument'):
                self.invokes[invoke['displayname']]['in'].append(arg['x:key'])
            for arg in invoke.find_all('inoutargument'):
                self.invokes[invoke['displayname']]['in_out'].append(arg['x:key'])

    def __get_xaml_configs(self):
        config_models = re.findall('config[\w]*\("[^"]*"\)\("[^"]*"\)', self.soup.prettify(), re.IGNORECASE)
        config_models_vb = re.findall('config[\w]*\(&quot;[^&quot;]*&quot;\)\(&quot;[^&quot;]*&quot;\)', self.soup.prettify(),
                                      re.IGNORECASE)
        config_models.extend(config_models_vb)
        for config_model in config_models:
            if '&quot;' in config_model:
                config_keys = re.findall('(?<=\(&quot;)[^&quot;]*(?=&quot;\))', config_model)
            else:
                config_keys = re.findall('(?<=\(")[^"]*(?="\))', config_model)
            if config_keys[0] not in self.module_configs.keys():
                self.module_configs[config_keys[0]] = []
            if config_keys[1] not in self.module_configs[config_keys[0]]:
                self.module_configs[config_keys[0]].append(config_keys[1])

    def check_xaml_config(self, common_config, response):
        self.__get_xaml_configs()
        wrongs_pairs = []
        for first_key in self.module_configs:
            for second_key in self.module_configs[first_key]:
                if first_key not in common_config.keys() or second_key not in common_config[first_key]:
                    wrongs_pairs.append(f'("{first_key}")("{second_key}")')

        response['used_config'] = self.module_configs
        response['module_wrongs']['config_pairs'] = wrongs_pairs

    @staticmethod
    def __skip_elements(tag):
        return tag.name not in definition_elements

    def __is_variable_use(self, var):
        for element in self.soup.find_all(self.__skip_elements):
            if bool(re.search(f'{var}', element.text)):
                return True
            for attr in element.attrs:
                if attr not in definition_attrs:
                    if bool(re.search(f'{var}', element[attr])):
                        return True

    def __add_if_hardcode(self, text):
        text_update = re.sub(r'&quot', '"', text)  # Remove (&quot; something &quot;)
        text_update = re.sub(r'\([^\(\)]*\)', '', text_update)  # Remove ("something", sadasdasd, dasdas)

        text_update = re.sub(r'\s', '', text_update)  # Remove spaces
        text_update = re.sub(r'""', '', text_update)  # Remove empty ""
        if bool(re.search(r'".*"', text_update)):
            if text.startswith('[') and text.endswith(']'):
                text = text[1:-1]
            if text not in self.hardcodes:
                self.hardcodes.append(text)

    def __check_hardcodes(self):
        for element in self.soup.find_all(self.__skip_elements):
            if "\n" not in element.text:
                self.__add_if_hardcode(element.text)

            for attr in element.attrs:
                if attr not in definition_attrs:
                    if '\n' not in element[attr]:
                        self.__add_if_hardcode(element[attr])
                    else:
                        if attr == 'code':
                            for line in element[attr]:
                                self.__add_if_hardcode(line)

    def __get_variables(self):
        for var in self.soup.find_all('variable'):
            self.variables.append(var['name'])
            if var.has_attr('x:typearguments') and var['x:typearguments'] == 'ui:GenericValue' and var['name'] not in self.generic_values:
                self.generic_values.append(var['name'])
        for arg in self.soup.find_all('x:property'):
            if arg['type'].lower().startswith('in'):
                key = 'in'
            if arg['type'].lower().startswith('out'):
                key = 'out'
            if arg['type'].lower().startswith('inout'):
                key = 'in_out'
            self.arguments[key].append(arg['name'])
            if arg.has_attr('x:typearguments') and arg['x:typearguments'] == 'ui:GenericValue' and arg[
                'name'] not in self.generic_values:
                self.generic_values.append(arg['name'])

    def __check_duplicates(self):
        displaynames = [tag['displayname'].strip() for tag in self.soup.find_all(displayname=True)]
        self.duplicates_names = list(set([name for name in displaynames if displaynames.count(name) > 1]))

    def check_xaml(self, response):
        self.__get_variables()
        for var in self.variables:
            if not self.__is_variable_use(var):
                self.unused_variables.append(var)
        for arg in (self.arguments['in'] + self.arguments['in_out']):
            if not self.__is_variable_use(arg):
                self.unused_arguments.append(arg)

        self.__check_hardcodes()

        response['module_wrongs']['vars'] = self.unused_variables
        response['module_wrongs']['args'] = self.unused_arguments
        response['module_wrongs']['generic_values'] = self.generic_values
        response['module_wrongs']['hardcodes'] = self.hardcodes
        response['module_wrongs']['duplicates'] = self.duplicates_names
