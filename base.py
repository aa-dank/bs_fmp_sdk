# constdoc_app/filemaker_integration.py

import json
import logging
import warnings
import fmrest
import pandas as pd

from urllib3.exceptions import InsecureRequestWarning
from typing import Dict, Any, List, Union, Optional, Callable

FILEMAKER_API_VERSION = 'v1'
FILEMAKER_PROJECTS_LAYOUT = 'projects_table'
FILEMAKER_TABLE_INDEX_COLUMN_NAME = 'ID_Primary'


class FileMakerDatabase:

    def __init__(self, url:str, user: str, password: str, database_name: str, api_version: str = 'v1', verify_ssl: bool = False):

        self.name = database_name
        self.user = user
        self.user_password = password
        self.url = url
        self.verify_ssl = verify_ssl
        self.api_version = api_version
        self.call_attempts = 3
        self.server = None

        # if we are making requests to filemaker, we do not have to be warned to use ssl
        warnings.filterwarnings('ignore', category=InsecureRequestWarning)

        # set request timeout in seconds
        fmrest.utils.TIMEOUT = 300

    def get_server(self, layout_name: str):
        def attempt_login():
            for attempt in range(self.call_attempts -1):
                try:
                    login_success = self.server.login()
                    if login_success:
                        return True
                except Exception as e:
                    except_str = f"""
                    While logging into {self.name} with user {self.user}, an error occurred:\n{e}
                    The Timeout: {fmrest.utils.TIMEOUT}
                    """
                    # if we have made all attempts, raise last function exception.
                    if attempt == self.call_attempts - 1:
                        raise Exception(except_str)
                    logging.info(except_str)
            return False

        if not self.server:
            self.server = fmrest.Server(url=self.url,
                                        user=self.user,
                                        password=self.user_password,
                                        database=self.name,
                                        layout=layout_name,
                                        api_version=self.api_version,
                                        verify_ssl=self.verify_ssl)

            attempt_login()

        else:
            # If the server is associated with a different layout, rebuild it for this layout
            if not self.server.layout == layout_name:
                if self.server._token:
                    self.server.logout()
                self.server = fmrest.Server(url=self.url,
                                            user=self.user,
                                            password=self.user_password,
                                            database=self.name,
                                            layout=layout_name,
                                            api_version=self.api_version,
                                            verify_ssl=self.verify_ssl)

            if not self.server._token:
                attempt_login()

        return self.server

    def attempt_fmrest_function(self, fmrest_funct_name: str, params_dict: Dict[str, Any], layout_for_funct: str = None,
                                assessment_funct: Optional[Callable] = None, logout_on_completion: bool = True):

        for attempt in range(self.call_attempts - 1):
            try:
                if not self.server or not self.server._token or not self.server.layout == layout_for_funct:
                    self.get_server(layout_name=layout_for_funct) #TODO use layout in server or in function call?
                fmrest_funct = getattr(self.server, fmrest_funct_name)
                attempt_results = fmrest_funct(**params_dict)

                assessment = True
                if assessment_funct:
                    assessment = assessment_funct(attempt_results)

                if assessment:
                    if logout_on_completion:
                        self.server.logout()
                    return attempt_results

            except Exception as e:
                except_str = f"""
                While performing {fmrest_funct_name}, an error occurred:\n{e}
                The Timeout: {fmrest.utils.TIMEOUT}
                """

                #if  we have made all attempts, logout and raise last function exception.
                if attempt == self.call_attempts - 1:
                    try:
                        self.server.logout()
                    except:
                        pass
                    raise Exception(e)

                # We will make different attempts at fixing fmrest and filemaker errors
                if type(e) == fmrest.exceptions.FileMakerError:

                    # If there is a bad token error...
                    if '952' in str(e):
                        try:
                            self.server.login()
                            continue
                        except Exception as ee:
                            except_str_addition = f"In attempt to resolve the above error by logging into the server another error was encountered:\n{ee}"
                            except_str = except_str + except_str_addition
                            logging.info(ee)
                            continue

                    # 401 error code means a successful query return no results
                    if '401' in str(e):
                        return None


    def get_layout_dataframe(self, layout_name: str, number_of_records: int) -> pd.DataFrame:
        params = {"limit": number_of_records}
        results = self.attempt_fmrest_function(fmrest_funct_name='get_records', params_dict=params,
                                               layout_for_funct=layout_name)
        df = results.to_df()
        return df

    def add_records_to_layout(self, layout_name: str, new_records_data: List[Dict[str, Any]]) -> List[bool]:
        new_record_results = []
        for idx, record_data in enumerate(new_records_data):
            log_out_yet = False
            params_dict = {"field_data": record_data}
            if idx == len(new_records_data)-1:
                log_out_yet = True
            record_created = self.attempt_fmrest_function(fmrest_funct_name='create_record',
                                                          params_dict=params_dict,
                                                          layout_for_funct=layout_name,
                                                          logout_on_completion=log_out_yet)
            new_record_results.append(record_created)
        return new_record_results

    def search_filemaker_layout(self, layout_name: str, query_data: List[Dict[str, Any]], limit: int = 10000):
        # https://github.com/davidhamann/python-fmrest/blob/master/examples/finding_data.ipynb
        params = {"query": query_data, "limit":limit}
        foundset = self.attempt_fmrest_function(fmrest_funct_name='find',
                                                params_dict=params,
                                                layout_for_funct=layout_name)
        return foundset

    def make_update_by_record(self, record, new_record_values: Dict):
        for field in list(new_record_values.keys()):
            record[field] = new_record_values[field]
        params = {"record": record, "layout": ""} #need to add layout somehow
        updated_successfully = self.attempt_fmrest_function(fmrest_funct_name='edit', params_dict=params,layout_for_funct=record)
        return updated_successfully

    def make_update_by_id(self, layout: str, record_num: str, new_record_values: Dict):
        # don't use
        params = {"record_id": record_num, "field_data":new_record_values}
        updated_successfully = self.attempt_fmrest_function(fmrest_funct_name='edit_record',
                                                            params_dict=params,
                                                            layout_for_funct=layout)
        return updated_successfully

    def retrieve_record_by_id_num(self, record_id: Union[str, int], layout: str):
        params = {"request_layout": layout,
                  "record_id":int(record_id)}
        record = self.attempt_fmrest_function(fmrest_funct_name='get_record',
                                              params_dict=params,
                                              layout_for_funct=layout)
        return record

    def execute_sql_query(self, layout: str, query: str, columns: List[str]) -> Dict[str, Any]:
        """
        Executes an SQL query on FileMaker by calling the ExecuteSQLQuery script.
        
        Parameters:
        layout (str): The layout context to run the script.
        query (str): The SQL SELECT query.
        columns (List[str]): A list of column names (or aliases) expected from the query.
        
        Returns:
        Dict[str, Any]: A dictionary containing the JSON result from the script,
                        typically with keys "columns" and "rows".
                        
        Raises:
        Exception: If there is an error performing the script or parsing the response.
        """
        # Build the JSON parameter as a string
        param_data = {
            "query": query,
            "columns": columns
        }
        param_json = json.dumps(param_data)
        
        # Ensure we're logged into the server with the proper layout
        self.get_server(layout_name=layout)
        
        # Call the FileMaker script "ExecuteSQLQuery" via the Data API using fmrest.
        # fmrest's perform_script method returns a tuple (error_code, script_result)
        try:
            error_code, script_result = self.server.perform_script("ExecuteSQLQuery", param=param_json)
        except Exception as e:
            raise Exception("Error performing script: " + str(e))
        
        if error_code and error_code != "0":
            raise Exception("FileMaker script returned an error: " + str(error_code))
        
        # Parse the returned JSON result into a Python dictionary.
        try:
            result_dict = json.loads(script_result)
        except Exception as e:
            raise Exception("Error parsing JSON response: " + str(e))
        
        return result_dict
