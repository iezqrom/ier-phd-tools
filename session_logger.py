import csv
from datetime import datetime
import os
import pandas as pd
import os
import ast

from systems import find_parent_folder
from text import printme

class SessionLogger:
    """
    A class to log experimental sessions by collecting various data points from the user
    and writing them to a logbook.
    """

    def __init__(self):
        self.file_names = [
            'logbook.csv', 'mice.csv', 'licenses.csv',
            'methods.csv', 'experimenters.csv', 'experimental_design.csv'
        ]
        self.paths = {
            os.path.splitext(file_name)[0]: find_parent_folder(file_name) for file_name in self.file_names
        }
        self.file_path = self.paths['logbook']
    
    def log_weight(self):
        """
        Logs the weight of the subject by adding an entry to the weight logbook.
        """
        # Subject ID
        mice_data_dict = self.get_csv_data(self.paths['mice'], 'mice.csv')
        mice_path = os.path.join(self.paths['mice'], 'mice.csv')
        mice_data_csv = pd.read_csv(mice_path)
        mice_options = [f"{value['subject_id']}" for _, value in mice_data_dict.items()]
        subject_number_id = self.get_input("Enter the ID of the subject", mice_options, start=0)
        # self.subject_number = subject_number_id.split()[0]
        self.subject_id = subject_number_id.split()[0]

        print(f"Subject ID: {self.subject_id}")

        # Weight data
        weight = input("Enter the weight of the subject (in grams): ")
        self.weight = int(weight) if weight.isdigit() else None
        try:
            self.weight = float(weight)
        except ValueError:
            self.weight = None

        # get the date in the format DD/MM/YYYY
        date = datetime.now().strftime('%d/%m/%Y')

        # Add the weight entry to the CSV
        # check whether there's a row for the subject_id in the CSV
        if mice_data_csv['subject_id'].isin([self.subject_id]).any():
            # Retrieve the current cell value
            current_value = mice_data_csv.loc[mice_data_csv['subject_id'] == self.subject_id, 'weight'].iloc[0]
            
            # Check if the cell is not empty and contains a dictionary
            if pd.notna(current_value):
                # Convert the string back to a dictionary
                current_dict = ast.literal_eval(current_value)
            else:
                # If the cell is empty, initialize a new dictionary
                current_dict = {}
            
            # Add the new date and weight
            current_dict[date] = self.weight
            
            # Convert the dictionary back to a string and update the DataFrame
            mice_data_csv.loc[mice_data_csv['subject_id'] == self.subject_id, 'weight'] = str(current_dict)

            # write the updated data to the CSV
            mice_data_csv.to_csv(mice_path, index=False)

            print(f"Weight of {self.weight} grams logged for subject {self.subject_id} on {date}.")
        else:
            print(f"Subject ID {self.subject_id} not found.")


    def define_session(self):
        """
        Logs a session by collecting various data points from the user and writing them to a logbook.
        """
        # Subject ID
        mice_data = self.get_csv_data(self.paths['mice'], 'mice.csv')
        mice_options = [f"{value['subject_id']}" for _, value in mice_data.items()]
        subject_number_id = self.get_input("Enter the ID of the subject", mice_options, start=0)
        self.subject_id = subject_number_id.split()[0]
        self.subject_number = self.get_subject_number(self.subject_id)

        print(f"Subject ID: {self.subject_id}, Subject number: {self.subject_number}")

        # License data
        license_data = self.get_csv_data(self.paths['licenses'], 'licenses.csv')
        self.license = self.get_input("Enter the license", list(license_data.keys()))
        subprojects = eval(license_data[self.license]['subprojects'])
        self.subproject = self.get_input("Enter the subproject", subprojects)

        # Method data
        method_data = self.get_csv_data(self.paths['methods'], 'methods.csv')
        self.method = self.get_input("Enter the method", list(method_data.keys()))
        method_versions = eval(method_data[self.method]['versions'])
        self.method_version = self.get_input("Enter the version", method_versions)

        # Experimenter data
        experimenter_data = self.get_csv_data(self.paths['experimenters'], 'experimenters.csv')
        self.experimenter = self.get_input("Enter the experimenter", list(experimenter_data.keys()))

        # Duration data
        duration = input("Enter the duration of the experiment (in seconds): ")
        self.duration_s = int(duration) if duration.isdigit() else None

        # Condition data
        condition_data = self.get_csv_data(self.paths['experimental_design'], 'experimental_design.csv')
        self.condition = self.get_input("Enter the condition", list(condition_data.keys()))

        # Additional notes
        self.notes = input("Enter additional notes: ")

    def log_session(self):
        """
        Logs the session by adding an entry to the logbook.
        """
        
        if self.subject_id is None and self.subject_number is None:
            raise ValueError("Either subject_id or subject_number must be provided.")
        elif self.subject_id is not None and self.subject_number is not None:
            # Optionally, you could add a check to ensure they match

            if int(self.get_subject_number(self.subject_id)) != int(self.subject_number):                
                raise ValueError("Provided subject_id and subject_number do not match.")
        
        name_logbook_file = 'logbook.csv'
        self.file_path = os.path.join(self.file_path, name_logbook_file)
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

        log_entry_data = [
            str(self.subject_id), str(self.subject_number), str(self.license), 
            str(self.subproject), str(self.method), str(self.method_version), str(self.duration_s),
            str(self.condition), str(self.experimenter), str(self.notes)
        ]
        log_entry_with_timestamp = self.append_timestamp(log_entry_data)

        try:
            file_exists = os.path.isfile(self.file_path)
            with open(self.file_path, mode='a', newline='') as file:
                writer = csv.writer(file)
                if not file_exists:
                    writer.writerow(['timestamp', 'subject_id', 'subject_number', 'license', 'subproject', 'method', 'method_version', 'duration_s', 'condition', 'experimenter', 'notes'])
                writer.writerow(log_entry_with_timestamp)
            print(f"Log entry added: {log_entry_with_timestamp}")
        except Exception as e:
            print(f"Error adding log entry: {e}")

    @staticmethod
    def append_timestamp(data):
        """
        Appends the current timestamp to the given data.

        Parameters:
            data (list): The data to which the timestamp will be appended.

        Returns:
            list: The data with the current timestamp appended at the beginning.
        """
        current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return [current_timestamp] + data


    def get_subject_number(self, subject_id, file_name='mice.csv'):
        """
        Given a subject_id, output the corresponding subject_number from the CSV file.

        Parameters:
            subject_id (str): ID of the subject.

        Returns:
            str: The subject number corresponding to the provided subject_id.
            None: If the subject_id is not found.
        """

        # Define the path to the CSV file
        file_path = os.path.join(self.paths['mice'], file_name)
        # Read the CSV file into a DataFrame
        df = pd.read_csv(file_path)
        # Search for the subject_id and get the corresponding subject_number
        subject_row = df[df['subject_id'] == subject_id]
        
        if not subject_row.empty:
            return subject_row.iloc[0]['subject_number']
        else:
            return None


    def get_subject_id(self, subject_number, file_name='mice.csv'):
        """
        Given a subject_number, output the corresponding subject_id from the CSV file.

        Parameters:
            subject_number (str): Number of the subject.

        Returns:
            str: The subject ID corresponding to the provided subject_number.
            None: If the subject_number is not found.
        """

        # Define the path to the CSV file
        file_path = os.path.join(self.paths['mice'], file_name)
        # Read the CSV file into a DataFrame
        df = pd.read_csv(file_path)
        # Search for the subject_number and get the corresponding subject_id
        subject_row = df[df['subject_number'] == subject_number]

        if not subject_row.empty:
            return subject_row.iloc[0]['subject_id']
        else:
            return None


    @staticmethod
    def get_csv_data(path, file_name):
        """
        Navigate up one directory, find the specified CSV file, and extract
        its data into a nested dictionary where the first column's values 
        are keys and the rest of the columns form the nested dictionary.

        Parameters:
            file_name (str): The name of the CSV file to read.

        Returns:
            dict: A nested dictionary where the first column's values are keys
                  and the rest of the columns form the nested dictionary.

        Raises:
            FileNotFoundError: If the specified CSV file does not exist in the 
                               parent directory.
        """
        # Define the path to the CSV file
        file_path = os.path.join(path, file_name)
        
        # Check if the file exists
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"The file {file_path} does not exist.")
        
        # Read the CSV file
        df = pd.read_csv(file_path)
        
        # Initialize the dictionary
        data_dict = {}
        
        # Populate the dictionary with the first column as keys and the rest as nested dictionaries
        first_column = df.columns[0]
        for _, row in df.iterrows():
            key = row[first_column]
            nested_dict = row.drop(first_column).to_dict()
            data_dict[key] = nested_dict
        
        return data_dict


    @staticmethod
    def get_input(prompt, options, start = 1):
        """
        Gets input from the user, allowing selection from a list of options.

        Parameters:
            prompt (str): The prompt to display to the user.
            options (list): The list of options to choose from.

        Returns:
            str: The option selected by the user.
        """
        printme(prompt)
        for i, option in enumerate(options):
            print(f"{i + start}. {option}")
        
        while True:
            user_input = input("Select an option by entering the corresponding number: ")
            if user_input.isdigit():
                index = int(user_input) - start
                if 0 <= index < len(options):
                    return options[index]
            printme("Invalid input, please enter a number corresponding to the options above.")
