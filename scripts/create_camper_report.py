import argparse
import polars as pl
import phonenumbers as pn
import pprint as pp

# list of questions to include in the roster report
ROSTER_QUESTIONS = [
    'Child\'s Last Name',
    'Child\'s First Name',
    'Gender',
    'Child\'s Age',
    'Entering Grade',
    'Allergies',
    'EPI-PEN?',
    'Returning Camper?',
    'T-Shirt Size'
]

# list of questions that contain phone numbers to
# be parsed into a consistent format
PHONE_NUMBER_QUESTIONS = [
    '1st Authorized Adult Contact Details Phone',
    '1st Parent/Guardian Contact Information Phone',
    '2nd Authorized Adult Contact Details Phone',
    '2nd Parent/Guardian Contact Information Phone',
    'Child\'s Physician Phone Number',
    'Emergency Contact Phone'
]

def parse_phone_number(phone_number):
    """
    Parse a phone number into a consistent format.

    Parameters
    ----------
    phone_number : str
        The phone number to be parsed.

    Returns
    -------
    str        
    """
    if phone_number is None or phone_number == '':
        return ''
    
    phone_number = pn.parse(phone_number, 'US')
    return pn.format_number(phone_number, pn.PhoneNumberFormat.INTERNATIONAL)

def main():
    """
    Create camper reports from an input file containing 
    camper responses to questions. 
    
    The input file should be a comma-separated file with 
    columns 'Name', 'Question', and 'Answer'.

    The script pivots the data to create two reports:
    1) a report where each row corresponds to a camper and each column 
    corresponds to a question (for all questions in the file), and
    2) a roster containing a selected list of questions for each camper.

    Usage
    -----
    % poetry run python create_camper_report.py <filename.csv>
    """
    # setup command line argument parsing
    parser = argparse.ArgumentParser(
                    prog='create_camper_report')
    parser.add_argument('filename', help='Full path to the input CSV file.')

    # get the filename from the command line arguments
    args = parser.parse_args()
    filename = args.filename

    # read the input file and pivot the data to create the camper report
    df = pl.read_csv(filename)

    # rename the columns to match the expected format
    df = df = df.rename({
        "Sales Order Item\\Sales Order Item Ticket\\Sales Order Item Ticket Registrant\\Registrant\\Name": "Name",
        "Sales Order Item\\Sales Order Item Ticket\\Sales Order Item Ticket Registrant\\Registrant\\Registration Information\\Question": "Question",
        "Sales Order Item\\Sales Order Item Ticket\\Sales Order Item Ticket Registrant\\Registrant\\Registration Information\\Response": "Response", 
    })

    # drop queryid column
    df = df.drop('QUERYRECID')

    # pivot the data to create the report dataset
    df = df.pivot(on='Question', index=['Name'], values='Response')

    # parse phone numbers into a consistent format  
    for question in PHONE_NUMBER_QUESTIONS:
        df = df.with_columns(
            pl.col(question).map_elements(parse_phone_number).alias(question)
        )

    # write the full camper report to a CSV file
    df.write_csv("camper_report_full.csv")
    
    # write the roster report to a CSV file, selecting only the specified questions
    df = df.select(ROSTER_QUESTIONS)
    df.write_csv("camper_roster.csv")
    
if __name__ == "__main__":
    main()

