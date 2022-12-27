import click
import requests
from tqdm import trange
from time import sleep

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
@click.option("--fullname", prompt="Enter your fullname", help="The fullname of the user")
def login(email, fullname):
    data_login = {"email": email}
    requests.post('https://api.restorage.io/api/rest/OTPAuth/Login', data=data_login)
    data_otp = {"email": email, "code": click.prompt("Please enter the code you've recieved", type=int)}
    response = requests.post('https://api.restorage.io/api/rest/OTPAuth/AuthenticateUser', data=data_otp)
    req = response.json()
    file = open('token.txt', "w")
    file.write(req['data']['token'])
    print("successfully logged in. use the --upload argument after this message")
    
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
            ids = [1,2,3,4]
            print(ids)
            click.prompt("please change the folder name or select the given ids")
    # print("Uploaded Successfully!")
    
   
myCommands.add_command(hello)
myCommands.add_command(login)
myCommands.add_command(upload)

if __name__ == "__main__":
    myCommands()