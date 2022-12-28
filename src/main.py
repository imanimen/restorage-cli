import click
import requests
from tqdm import trange
from time import sleep
import json

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
    login = requests.post('https://api.restorage.io/api/rest/OTPAuth/Login', data=data_login)
    print(login.content)
    data_otp = {"email": email, "code": click.prompt("Please enter the code you've recieved", type=int)}
    response = requests.post('https://api.restorage.io/api/rest/OTPAuth/AuthenticateUser', data=data_otp)
    req = response.json()
    if req['code'] == 200:
        file = open('src/token.txt', "x")
        file.write(req['data']['token'])
        print("successfully logged in.")
        
    else:
        for i in req['messages']:
            data_otp = {"email": email, "code": click.prompt(f"{i} Try again", type=int)}
            response = requests.post('https://api.restorage.io/api/rest/OTPAuth/AuthenticateUser', data=data_otp)
            req = response.json()
            if req['code'] == 200:
                file = open('token.txt', "x")
                file.write(req['data']['token'])
                print("successfully logged in.")
    
@click.command()
@click.option("--folder", prompt="Enter the folder name", help="the folder name")
# @click.option("--file", prompt="Enter your file", help="The fullname of the user")
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
            
            click.prompt("please change the folder name or select the given ids")
    # print("Uploaded Successfully!")
    
   
myCommands.add_command(hello)
myCommands.add_command(login)
myCommands.add_command(upload)

if __name__ == "__main__":
    myCommands()