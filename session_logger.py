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
            'logbook.csv', 'subjects.csv', 'licenses.csv',
            'methods.csv', 'experimenters.csv', 'experimental_design.csv',
            'genotypes.csv'
        ]
        self.paths = {
            os.path.splitext(file_name)[0]: os.path.join(find_parent_folder(file_name), file_name) for file_name in self.file_names
        }

        self.subject_id = None
        self.subject_number = None
        self.license = None
        self.subproject = None
        self.method = None
        self.method_version = None
        self.duration_s = None
        self.condition = None
        self.experimenter = None
        self.notes = None


    def get_subject_id_and_number(self):
        """
        Prompts user to enter the subject ID and retrieves the corresponding subject number.
        """
        subjects_data_dict = self.get_csv_data(self.paths['subjects'])
        subjects_options = [f"{value['subject_id']}" for _, value in subjects_data_dict.items()]
        subject_number_id = self.get_input("Enter the ID of the subject", subjects_options, start=0)
        self.subject_id = subject_number_id.split()[0]
        self.subject_number = self.get_subject_number(self.subject_id)

        printme(f"Subject ID: {self.subject_id}, Subject number: {self.subject_number}")


    def get_license_data(self):
        """
        Retrieves the license data for the subject.
        """

        subjects_data_csv = pd.read_csv(self.paths['subjects'])
        self.current_license = subjects_data_csv[subjects_data_csv['subject_id'] == self.subject_id]['current_license'].iloc[0]
        if self.current_license in ['ZH_139', 'X9016_21', 'G0167_23']:
            license_data = self.get_csv_data(self.paths['licenses'])
            self.current_license = self.get_input("Enter the license", list(license_data.keys()))

        printme(f"License: {self.current_license}")


    def get_subproject_data(self):
        """
        Retrieves the subproject data for the subject.
        """
        subjects_path = os.path.join(self.paths['subjects'])
        subjects_data_csv = pd.read_csv(subjects_path)
        self.current_subproject = subjects_data_csv[subjects_data_csv['subject_id'] == self.subject_id]['current_subproject'].iloc[0]
        if self.current_subproject is None:
            license_data = self.get_csv_data(self.paths['licenses'])
            subprojects = eval(license_data[self.license]['subprojects'])
            self.current_subproject = self.get_input("Enter the subproject", subprojects)

        printme(f"Subproject: {self.current_subproject}")
    

    def get_method_data(self):
        """
        Prompts user to select method and returns it.
        """
        if self.method is None:
            method_data = self.get_csv_data(self.paths['methods'])
            self.method = self.get_input("Enter the method", list(method_data.keys()))

        printme(f"Method: {self.method}")


    def get_method_version_data(self):
        """
        Prompts user to select method version and returns it.
        """
        if self.method_version is None:
            method_data = self.get_csv_data(self.paths['methods'])
            method_versions = eval(method_data[self.method]['versions'])
            self.method_version = self.get_input("Enter the version", method_versions)
        
        printme(f"Method version: {self.method_version}")


    def get_experimenter_data(self):
        """
        Prompts user to select experimenter and returns it.
        """
        if self.experimenter is None:
            experimenter_data = self.get_csv_data(self.paths['experimenters'])
            self.experimenter = self.get_input("Enter the experimenter", list(experimenter_data.keys()))

        printme(f"Experimenter: {self.experimenter}")

    def get_condition_data(self):
        """
        Retrieves the condition data for the subject.
        """
        self.condition = self.get_mouse_condition()
        if self.condition is None:
            condition_data = self.get_csv_data(self.paths['experimental_design'])
            self.condition = self.get_input("Enter the condition", list(condition_data.keys()))

        printme(f"Condition: {self.condition}")


    def get_duration_data(self):
        """
        Prompts user to enter duration of the experiment and returns it.
        """
        if self.duration_s is None:
            duration = input("Enter the duration of the experiment (in seconds): ")
            self.duration_s = int(duration) if duration.isdigit() else None

        printme(f"Duration: {self.duration_s} seconds")


    def get_notes_data(self):
        """
        Prompts user to enter additional notes and returns it.
        """
        if self.notes is None:
            self.notes = input("Enter additional notes: ")

        printme(f"Notes: {self.notes}")
    

    def define_session(self):
        """
        Logs a session by collecting various data points from the user and writing them to a logbook.
        """
        self.get_subject_id_and_number()

        self.get_license_data()
        
        self.get_subproject_data()

        self.get_method_data()

        self.get_method_version_data()

        self.get_experimenter_data()

        self.get_condition_data()

        self.get_duration_data()


    def define_multiple_sessions(self):
        """
        Logs multiple sessions for selected subject IDs with common parameters.
        """
        subject_ids = self.select_multiple_subjects()
        self.get_method_data()
        self.get_method_version_data()
        self.get_experimenter_data()
        self.get_duration_data()
        self.get_notes_data()
        for subject_id in subject_ids:
            self.subject_id = subject_id
            self.subject_number = self.get_subject_number(subject_id)

            # License data
            self.license = self.get_current_license()

            # Subproject data
            self.subproject = self.get_current_subproject()

            # Condition data
            self.condition = self.get_mouse_condition()

            # Log the session
            self.log_session()


    def log_weight(self):
        """
        Logs the weight of the subject by adding an entry to the weight logbook.
        """
        # Subject ID
        subjects_data_dict = self.get_csv_data(self.paths['subjects'])
        subjects_data_csv = pd.read_csv(self.paths['subjects'])
        subjects_options = [f"{value['subject_id']}" for _, value in subjects_data_dict.items()]
        subject_number_id = self.get_input("Enter the ID of the subject", subjects_options, start=0)
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
        if subjects_data_csv['subject_id'].isin([self.subject_id]).any():
            # Retrieve the current cell value
            current_value = subjects_data_csv.loc[subjects_data_csv['subject_id'] == self.subject_id, 'weight'].iloc[0]
            
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
            subjects_data_csv.loc[subjects_data_csv['subject_id'] == self.subject_id, 'weight'] = str(current_dict)

            # write the updated data to the CSV
            subjects_data_csv.to_csv(self.paths['subjects'], index=False)

            self.license = self.get_current_license()
            self.subproject = self.get_current_subproject()
            self.method = 'weighing'
            self.method_version = '101'
            self.duration_s = 60
            self.condition = self.get_mouse_condition()
            self.experimenter = 'IER'
            self.notes = f"Weight of {str(self.weight)} grams"
            self.log_session()

            print(f"Weight of {self.weight} grams logged for subject {self.subject_id} on {date}.")
        else:
            print(f"Subject ID {self.subject_id} not found.")


    def get_current_license(self):
        """
        Given a subject_id, output the corresponding license from the CSV file.

        Parameters:
            subject_id (str): ID of the subject.

        Returns:
            str: The license corresponding to the provided subject_id.
            None: If the subject_id is not found.
        """

        # Read the CSV file into a DataFrame
        df = pd.read_csv(self.paths['subjects'])
        # Search for the subject_id and get the corresponding license
        subject_row = df[df['subject_id'] == self.subject_id]
        
        if not subject_row.empty:
            return subject_row.iloc[0]['current_license']
        else:
            return None


    def get_current_subproject(self):
        """
        Given a subject_id, output the corresponding subproject from the CSV file.

        Parameters:
            subject_id (str): ID of the subject.

        Returns:
            str: The subproject corresponding to the provided subject_id.
            None: If the subject_id is not found.
        """

        # Read the CSV file into a DataFrame
        df = pd.read_csv(self.paths['subjects'])
        # Search for the subject_id and get the corresponding subproject
        subject_row = df[df['subject_id'] == self.subject_id]
        
        if not subject_row.empty:
            return subject_row.iloc[0]['current_subproject']
        else:
            return None


    def get_mouse_condition(self):
        """
        Given a subject_id, output the corresponding condition from the CSV file.

        Returns:
            str: The condition corresponding to the provided subject_id.
            None: If the subject_id is not found.
        """

        if self.license != 'ZH_139' or self.license != 'X9016_21' or self.license != 'G0167_23':

            # Read the CSV file into a DataFrame
            df = pd.read_csv(self.paths['experimental_design'])
            
            # Convert the 'subjects' column from string to list
            df['subjects'] = df['subjects'].apply(ast.literal_eval)

            subject_row = df[df['subjects'].apply(lambda x: self.subject_id in x)]
            print(subject_row)
            if not subject_row.empty:
                return subject_row.iloc[0]['condition']
            else:
                return None


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
        
        os.makedirs(os.path.dirname(self.paths['logbook']), exist_ok=True)

        log_entry_data = [
            str(self.subject_id), str(self.subject_number), str(self.license), 
            str(self.subproject), str(self.method), str(self.method_version), str(self.duration_s),
            str(self.condition), str(self.experimenter), str(self.notes)
        ]
        log_entry_with_timestamp = self.append_timestamp(log_entry_data)

        try:
            file_exists = os.path.isfile(self.paths['logbook'])
            with open(self.paths['logbook'], mode='a', newline='') as file:
                writer = csv.writer(file)
                if not file_exists:
                    writer.writerow(['timestamp', 'subject_id', 'subject_number', 'license', 'subproject', 'method', 'method_version', 'duration_s', 'condition', 'experimenter', 'notes'])
                writer.writerow(log_entry_with_timestamp)
            print(f"Log entry added: {log_entry_with_timestamp}")
        except Exception as e:
            print(f"Error adding log entry: {e}")


    def add_subjects(self):
        """
        Adds new subjects to the subjects.csv file.
        """
        subjects_data_csv = pd.read_csv(self.paths['subjects'])
        genotypes_data_csv = pd.read_csv(self.paths['genotypes'])

        new_subjects = []

        while True:
            subject = {}

            # Add subject ID
            while True:
                subject_id = input("Enter the subject ID: ")
                confirmation = input(f"Confirm subject ID '{subject_id}' (y/n): ").lower()
                if confirmation == 'y':
                    subject['subject_id'] = subject_id
                    break
                elif confirmation == 'n':
                    continue

            # Confirm adding more subjects
            add_more_ids = input("Do you want to add more IDs? (y/n): ").lower()
            if add_more_ids == 'n':
                break

        while True:
            # Add sex
            sex = self.get_input("Enter the sex (male/female): ", ["male", "female"])
            subject['sex'] = sex

            # Add date of birth
            while True:
                date_of_birth = input("Enter the date of birth (DD/MM/YYYY): ")
                try:
                    datetime.strptime(date_of_birth, '%d/%m/%Y')
                    subject['date_of_birth'] = date_of_birth
                    break
                except ValueError:
                    printme("Invalid date format. Please enter in DD/MM/YYYY format.")

            # Add cage number
            existing_cage_numbers = subjects_data_csv['cage_number'].unique().tolist()
            cage_number = self.get_input("Enter the cage number or select from existing:", existing_cage_numbers + ["Enter new value"])
            if cage_number == "Enter new value":
                cage_number = input("Enter new cage number: ")
            subject['cage_number'] = cage_number

            # Add species
            unique_species = genotypes_data_csv['species'].unique().tolist()
            species = self.get_input("Enter the species:", unique_species)
            subject['species'] = species

            # Add genotype
            genotypes_for_species = genotypes_data_csv[genotypes_data_csv['species'] == species]['genotype'].unique().tolist()
            genotype = self.get_input("Enter the genotype:", genotypes_for_species)
            subject['genotype'] = genotype

            # Default fields
            subject['current_license'] = 'ZH_139'
            subject['current_subproject'] = ''
            subject['notes'] = input("Enter any notes: ")

            # Repository and weight fields left empty
            subject['repository'] = ''
            subject['weight'] = ''

            new_subjects.append(subject)

            # Confirm adding more subjects
            add_more_subjects = input("Do you want to add another subject? (y/n): ").lower()
            if add_more_subjects == 'n':
                break

        # Generate subject_number for each new subject
        last_subject_number = subjects_data_csv['subject_number'].max()
        for i, subject in enumerate(new_subjects):
            subject['subject_number'] = last_subject_number + 1 + i

        # Append new subjects to the CSV
        new_subjects_df = pd.DataFrame(new_subjects)
        subjects_data_csv = pd.concat([subjects_data_csv, new_subjects_df], ignore_index=True)
        subjects_data_csv.to_csv(self.paths['subjects'], index=False)

        printme("New subjects added successfully.")


    def select_multiple_subjects(self):
        """
        Displays all subject IDs and allows the user to select multiple subjects.

        Returns:
            list: A list of selected subject IDs.
        """
        subjects_data_dict = self.get_csv_data(self.paths['subjects'])
        subjects_options = [f"{value['subject_id']}" for _, value in subjects_data_dict.items()]

        printme("Select the IDs of the subjects (separated by commas):")
        for i, option in enumerate(subjects_options):
            print(f"{i + 1}. {option}")

        while True:
            user_input = input("Enter the numbers corresponding to the subjects, separated by commas: ")
            try:
                selected_indices = [int(x) - 1 for x in user_input.split(',')]
                selected_ids = [subjects_options[i] for i in selected_indices]
                print(selected_ids)
                return selected_ids
            except (ValueError, IndexError):
                printme("Invalid input, please enter valid numbers corresponding to the subjects.")


    def get_subject_number(self, subject_id):
        """
        Given a subject_id, output the corresponding subject_number from the CSV file.

        Parameters:
            subject_id (str): ID of the subject.

        Returns:
            str: The subject number corresponding to the provided subject_id.
            None: If the subject_id is not found.
        """

        # Read the CSV file into a DataFrame
        df = pd.read_csv(self.paths['subjects'])
        # Search for the subject_id and get the corresponding subject_number
        subject_row = df[df['subject_id'] == subject_id]
        
        if not subject_row.empty:
            return subject_row.iloc[0]['subject_number']
        else:
            return None


    def get_subject_id(self, subject_number):
        """
        Given a subject_number, output the corresponding subject_id from the CSV file.

        Parameters:
            subject_number (str): Number of the subject.

        Returns:
            str: The subject ID corresponding to the provided subject_number.
            None: If the subject_number is not found.
        """

        # Read the CSV file into a DataFrame
        df = pd.read_csv(self.paths['subjects'])
        # Search for the subject_number and get the corresponding subject_id
        subject_row = df[df['subject_number'] == subject_number]

        if not subject_row.empty:
            return subject_row.iloc[0]['subject_id']
        else:
            return None


    @staticmethod
    def get_csv_data(file_path):
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
