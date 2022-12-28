import click
import requests
import json
import os
import colorama

from dotenv import load_dotenv


load_dotenv()
OTP_LOGIN_URL=os.getenv('OTP_LOGIN_URL')
OTP_AUTH_URL=os.getenv('OTP_AUTH_URL')
UPLAOD_URL=os.getenv('UPLAOD_URL')
UPLOAD_FOLDERS=os.getenv('UPLOAD_FOLDERS')

@click.group()
def myCommands():
    pass

# @click.clear()
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
@click.option("--folder", prompt="Enter the folder name", help="the folder name")
@click.argument('file', type=click.File('rb'))
def upload(file, folder):
    token = open('token.txt', 'r')
    headers = {'Accept': "Application/json", 'Authorization': 'Bearer '+token.read()}
    files = {'files[]': file}
    data  = {'folder_name': folder}
    response = requests.post('https://api.restorage.io/api/rest/Restorage/UploadFile', data=data, files=files, headers=headers)
    req = response.json()
    if req['code'] != 200:
        for message in req['messages']:
            print(message)
            user_folders = requests.get(UPLOAD_FOLDERS, headers=headers)
            user_folders_list = user_folders.json()
            click.echo(click.style('These are your folders. Either select one of them or re-run the command and give the folder name.', fg='green'))
            for i in user_folders_list['data']:
                print(i['id'],i['name'])
            data_upload = {"files[]": file, "folder_id": click.prompt("Please enter the folder id", type=int)}
            request = requests.post('https://api.restorage.io/api/rest/Restorage/UploadFile', data=data_upload, files=files, headers=headers)
            click.echo(request.content)
            
    
   
myCommands.add_command(hello)
myCommands.add_command(login)
myCommands.add_command(upload)

if __name__ == "__main__":
    myCommands()