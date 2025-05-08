# -*- coding: utf-8 -*-
"""Create Qualtrics survey for chatbot intervention

To use, go to Qualtrics and export the TEMPLATE survey in it's QSF format.

This function creates a new survey and adds the survey id into a MySQL DB.

There is also code to activate surveys, move surveys to folders, and add javascript to surveys.
"""


from future import __annotations__

import requests
from pathlib import Path
from datetime import datetime
from sqlalchemy import create_engine, text

from sqlalchemy.engine.base import Engine


"""## Survey Settings"""

QUALTRICS_DATACENTER_ID = 'something' # "ca1" is the NYU data_center_id
QUALTRICS_API_TOKEN = 'something' # "ca1" is the NYU data_center_id
TEMPLATE_FILE_PATH: str = 'test-chatbot-survey-template.qsf'  # NEEDS TO BE UPLOADED FROM COMPUTER!!!
QUESTION_ID = "QID58"  # The question id of the iframe question. This is hardcoded. It should be dynamic.
today = datetime.now().strftime('%Y-%m-%d')

SURVEY_NAME_TEMPLATE: str = f"test-chatbot-survey-{datetime.now().strftime('%Y-%m-%d')}" # The name of the surveys. {article_num} is an incrementing number.

BASE_URL: str = f'https://{data_center_id}.qualtrics.com/API/v3'.format(data_center_id = QUALTRICS_DATACENTER_ID)  # "ca1" is the NYU data_center_id
HEADERS: dict[str, str] = {'X-API-TOKEN': QUALTRICS_API_TOKEN}  # PUT YOUR QUALTRICS API KEY HERE

DB_SCHEMA: str = 'test'  # The schema of the database
DB_USER: str = 'test'
DB_PASSWOERD: str = 'some-password'
DB_HOST: str = 'some-host'
DB_PORT: int = 3306
DB_ENCODING: str = 'utf-8'

# The url of the chatbot server. {sub_domain} is a subdomain of your domain.
DOMAIN = 'chateval.org'
chatbot_server_url = 'https://{sub_domain}.{DOMAIN}'  

# The format that the javascript in the iframe (that runs Mephisto) is expecting from the Qualtrics url query string paramaters. MAY NEED TO CHANGE THIS.
WORKERID_FORMAT: str = "workerId"
ASSIGNMENTID_FORMAT: str = "assignmentId"
RESPONSEID_FORMAT: str = "responseId"


"""### Setup code"""



def iframe_template(url: str, workerid_format: str, 
                    assignmentid_format: str,
                    reponse_id_format: str) -> dict:
    """
    Template for iframe
    """

    return {"QuestionText":
            f'''<!DOCTYPE html>
                <html>
                    <body>
                        <iframe id="chatbotIframe"
                                allowfullscreen=""
                                frameborder="0"
                                marginwidth="0"
                                marginheight="0"
                                scrolling="NO"
                                style="width: min(75vw, 1400px); height: 100vh;">
                        </iframe>
                    </body>
                    <script>
                        const DOMAIN = "{url}";
                        const WORKERID_FORMAT = "{workerid_format}";
                        const ASSIGNMENTID_FORMAT = "{assignmentid_format}";
                        const RESPONSEID_FORMAT = "{reponse_id_format}";

                        const params = new URLSearchParams(document.location.search);

                        const workerID = params.get(WORKERID_FORMAT) || "workerid-not-found";
                        const assignmentID = params.get(ASSIGNMENTID_FORMAT) || "assignmentid-not-found";
                        const responseID = params.get(RESPONSEID_FORMAT) || "responseid-not-found";

                        const chatbotIframe = document.getElementById("chatbotIframe");
                        chatbotIframe.src = DOMAIN + '?worker_id=' + workerID + '&assignment_id=' + assignmentID + '&response_id=' + responseID;
                    </script>
                </html>
            ''',
            "DefaultChoices":False,
            "DataExportTag":"chatbot_display_container", # Important
            "QuestionType":"DB",
            "Selector":"TB",
            "Configuration":{
                "QuestionDescriptionOption":"UseText"
            },
            "QuestionDescription":"Chatbot section container",
            "ChoiceOrder":[

            ],
            "Validation":{
                "Settings":{
                    "Type":"None"
                }
            },
            "GradingData":[],
            "Language":[],
            "NextChoiceId":4,
            "NextAnswerId":1,
            "QuestionID": QUESTION_ID, # "QID58", # BUG: This is hardcoded. It should be dynamic.
            "DataVisibility":{
                "Private":False,
                "Hidden":False
            }
        }


def update_survey_template(survey_id, 
                           headers, 
                           qualtrics_api_url, 
                           chatbot_server_url, 
                           workerid_format, 
                           assignmentid_format,
                           reponseid_format):

    # Update Iframe question
    resp = requests.put(
        f'{qualtrics_api_url}/survey-definitions/{survey_id}/questions/{QUESTION_ID}', 
        headers=headers,
        json=iframe_template(url=chatbot_server_url, 
                             workerid_format=workerid_format, 
                             assignmentid_format=assignmentid_format,
                             reponseid_format=reponseid_format)
    )



def create_survey(*,
        article_row: tuple,
        headers: dict[str, str],
        qualtrics_api_url: str,
        sql_engine: Engine,
        template_path: str,
        template_name: str,
        survey_name_template: str,
        chatbot_server_url: str,
        subdomain: str,
        participants_needed: int,
        workerid_format: str,
        assignmentid_format: str,
        reponseid_format: str
    ) -> None:
    """Creates a survey from a .qsf template..."""

    data = {
        'name': survey_name_template.format(article_num=article_row[0])
        }
    files = {
        'file': (template_name, open(template_path, 'rb'), 'application/vnd.qualtrics.survey.qsf')
        }

    # Make survey
    resp = requests.post(f'{qualtrics_api_url}/surveys', files=files, data=data, headers=headers)

    if resp.status_code != 200:
        return resp.content

    survey_id = resp.json()['result']['id']

    # Update survey
    update_survey_template(survey_id, article_row, headers, qualtrics_api_url, chatbot_server_url, workerid_format, assignmentid_format)

    # Add survey to survey_info table in empathic_conversations_2 schema
    # add_row_to_survey_info_table(
    #     survey_id=survey_id, sql_engine=sql_engine,
    #     participants_needed=participants_needed,
    #     article_id=article_row[0], subdomain=subdomain
    # )

    return f'Done creating survey {survey_id}'



"""## Create Surveys

"""

conn_string = 'mysql://{user}:{password}@{host}:{port}/{db}?charset:{encoding}'.format(
    user=DB_USER, password=DB_PASSWOERD, host=DB_HOST, port=DB_PORT,
    db=DB_SCHEMA, encoding=DB_ENCODING
)

sql_engine = create_engine(conn_string)


result = create_survey(
    headers=HEADERS,
    qualtrics_api_url=BASE_URL,
    sql_engine=sql_engine,
    survey_name_template=SURVEY_NAME_TEMPLATE,
    chatbot_server_url=url,
    subdomain=subdomain,
    workerid_format=WORKERID_FORMAT,
    assignmentid_format=ASSIGNMENTID_FORMAT,
    reponseid_format=RESPONSEID_FORMAT
)

print(f'{result} on {url}')

"""## Create list of survey ids (survey_ids variable)

If you already have article in the database, then you may need to alter the query.
"""

conn_string = 'mysql://{user}:{password}@{host}:{port}/{db}?charset:{encoding}'.format(
    user=DB_USER, password=DB_PASSWOERD, host=DB_HOST, port=DB_PORT,
    db=DB_SCHEMA, encoding=DB_ENCODING)
engine = create_engine(conn_string)



"""## Activate Surveys"""

dataCenter = 'ca1'
data = {"isActive": True}
headers = {
        'content-type': 'application/json',
}
headers.update(HEADERS) # Add API key from above.

for id, _ in survey_ids:
    base_url = f'https://{dataCenter}.qualtrics.com/API/v3/surveys/{id}'
    response = requests.put(base_url, json=data, headers=headers)
    print(response.text)

dataCenter = 'ca1'
data = {"isActive": True}
headers = {
        'content-type': 'application/json',
}
headers.update(HEADERS) # Add API key from above.

base_url = f'https://{dataCenter}.qualtrics.com/API/v3/surveys/{id}'
response = requests.put(base_url, json=data, headers=headers)
print(response.text)



def surveys_to_db(survey_ids, engine):
    surveys = pd.DataFrame(survey_ids, columns=['survey_id'])
    surveys.to_sql('qualtrics_surveys', index=False, con=engine)

import requests
import zipfile
import json
import io, os
import sys
import time


id = "SV_6kWXVacTTAxB7f0"
dataCenter = 'az1'

def download_survey(id, dataCenter='az1'):
    # Setting static parameters
    requestCheckProgress = 0.0
    progressStatus = "inProgress"
    url = f"https://{dataCenter}.qualtrics.com/API/v3/surveys/{id}/export-responses/"
    headers = {
            'content-type': 'application/json',
    }
    headers.update(HEADERS) # Add API key from above.

    # Step 1: Creating Data Export
    data = {
            "format": "csv",
            "seenUnansweredRecode": 2
        }

    downloadRequestResponse = requests.request("POST", url, json=data, headers=headers)
    #print(downloadRequestResponse.json())

    try:
        progressId = downloadRequestResponse.json()["result"]["progressId"]
    except KeyError:
        print(downloadRequestResponse.json())
        return False

    isFile = None

    max_retries = 5
    retry_count = 0

    # Step 2: Checking on Data Export Progress and waiting until export is ready
    while progressStatus != "complete" and progressStatus != "failed" and isFile is None:
        if isFile is None:
            print("File not ready")
        else:
            print("ProgressStatus=", progressStatus)

        requestCheckUrl = url + progressId
        requestCheckResponse = requests.request("GET", requestCheckUrl, headers=headers)

        try:
            isFile = requestCheckResponse.json()["result"]["fileId"]
        except KeyError:
            pass

        print(requestCheckResponse.json())
        requestCheckProgress = requestCheckResponse.json()["result"]["percentComplete"]
        print("Download is " + str(requestCheckProgress) + " complete")
        progressStatus = requestCheckResponse.json()["result"]["status"]

        if progressStatus not in ["complete", "failed"]:
            # Implement exponential backoff with a maximum number of retries
            retry_count += 1
            if retry_count > max_retries:
                print("Exceeded maximum retries. Exiting.")
                return False

            # Calculate the next sleep interval using exponential backoff (The first retry will occur after 200 seconds, the second after 400 seconds, the third after 600 seconds, and so on, until the max_retries limit is reached)
            sleep_interval = 60 ** retry_count
            print(f"Retrying for survey {id} in {sleep_interval} seconds...")
            time.sleep(sleep_interval)

    # Step 3: Downloading file
    fileId = requestCheckResponse.json()["result"]["fileId"]
    requestDownloadUrl = url + fileId + '/file'
    requestDownload = requests.request("GET", requestDownloadUrl, headers=headers, stream=True)

    # Step 4: Unzipping the file
    zipfile.ZipFile(io.BytesIO(requestDownload.content)).extractall(f"survey_download_{id}")
    print('Complete')
    return True

# # This is an EC style qualification instead of the bot based qual.
# download_survey('SV_3jDybKbQyL07nvw')

import concurrent.futures

# Function to download surveys in parallel
def download_surveys_in_parallel(survey_ids):
    results = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_survey = {executor.submit(download_survey, survey_id): survey_id for survey_id in survey_ids}
        for future in concurrent.futures.as_completed(future_to_survey):
            survey_id = future_to_survey[future]
            try:
                data = future.result()
                results.append((survey_id, data))
            except Exception as exc:
                print(f"Survey {survey_id} generated an exception: {exc}")
    return results

# Run the parallel download
downloaded_surveys = download_surveys_in_parallel([_[0] for _ in survey_ids[5:]])
print(downloaded_surveys)


from glob import glob

filenames = glob('survey_download_SV_*/*.csv')

import pandas as pd
import re

surveys = pd.DataFrame()
for filename in filenames:
    df = pd.read_csv(filename, header=0, skiprows=[1,2])
    surveys = pd.concat([surveys, df])

surveys[surveys.Finished==1].to_sql('qualtrics_surveys', index=False, con=engine)
