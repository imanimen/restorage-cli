import click
import requests
import json
import os
import colorama
import shutil
import subprocess
from dotenv import load_dotenv

load_dotenv()
OTP_LOGIN_URL = os.getenv('OTP_LOGIN_URL')
OTP_AUTH_URL = os.getenv('OTP_AUTH_URL')
UPLAOD_URL = os.getenv('UPLAOD_URL')
UPLOAD_FOLDERS = os.getenv('UPLOAD_FOLDERS')


@click.group()
def myCommands():
    pass


"""
Authentication
"""


@click.command()
@click.option("--name", prompt="Enter your name", help="The name of the user")
@click.option("--code", prompt="Enter your code", help="The name of the user")
def hello(name, code):
    click.echo(f"Hello {name} {code}")


@click.command()
@click.option("--email", prompt="Enter your email", help="The email of the user")
def login(email):
    data_login = {"email": email}
    login = requests.post(OTP_LOGIN_URL, data=data_login)
    print(login.content)
    data_otp = {"email": email, "code": click.prompt("Please enter the code you've recieved", type=int)}
    response = requests.post(OTP_AUTH_URL, data=data_otp)
    req = response.json()
    if req['code'] == 200:
        file = open('token.txt', "x")
        file.write(req['data']['token'])
        print("successfully logged in.")

    else:
        for i in req['messages']:
            data_otp = {"email": email, "code": click.prompt(f"{i} Try again", type=int)}
            response = requests.post(OTP_AUTH_URL, data=data_otp)
            req = response.json()
            if req['code'] == 200:
                file = open('token.txt', "x")
                file.write(req['data']['token'])
                print("successfully logged in.")


@click.command()
@click.argument('folder', type=str)
@click.argument('files_ar', type=click.Path())
def upload(files_ar, folder):
    main_file = str(os.path.abspath(files_ar))
    COPY = ['cp', main_file, '/home/iman/Desktop/restorage-cli/src/uploads/']
    subprocess.run(COPY)
    token = open('token.txt', 'r')
    headers = {'Accept': "Application/json", 'Authorization': 'Bearer ' + token.read()}
    files = {'files[]': open(main_file, 'rb')}
    data = {'folder_name': folder}
    response = requests.post('https://api.restorage.io/api/rest/Restorage/UploadFile', data=data, files=files, headers=headers)
    req = response.json()
    # os.remove('/home/iman/Desktop/restorage-cli/src/uploads/'+os.path.basename(main_file))

    if req['code'] == 401:
        click.echo(click.style("Errors: "+req['errors'], fg='red'))
    elif req['code'] == 422:
        for messages in req['messages']:
            print(messages)
            user_folders = requests.get(UPLOAD_FOLDERS, headers=headers)
            user_folders_list = user_folders.json()
            click.echo(click.style(
                'These are your folders. Either select one of them or re-run the command and give the folder name.',
                fg='green', blink=True))
            for i in user_folders_list['data']:
                print(i['id'], i['name'])
            data_upload = {"folder_id": click.prompt("Please enter the folder id", type=int)}

        upload_files = {"files[]": open('/home/iman/Desktop/restorage-cli/src/uploads/'+os.path.basename(main_file), 'rb')}
        request = requests.post('https://api.restorage.io/api/rest/Restorage/UploadFile', data=data_upload,
                                    files=upload_files, headers=headers)
        res = request.json()
        if res['code'] == 200:
            click.echo(click.style('Uplaoded Successfully', fg='green'))
            os.remove('/home/iman/Desktop/restorage-cli/src/uploads/'+os.path.basename(main_file))

myCommands.add_command(hello)
myCommands.add_command(login)
myCommands.add_command(upload)

if __name__ == "__main__":
    myCommands()