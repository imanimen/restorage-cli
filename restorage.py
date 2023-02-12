import subprocess
import click
import requests
import os
import sys
from datetime import datetime


OTP_LOGIN_URL = "https://api.restorage.io/api/rest/OTPAuth/Login"
OTP_AUTH_URL = "https://api.restorage.io/api/rest/OTPAuth/AuthenticateUser"
USER_FOLDERS = "https://api.restorage.io/api/rest/Restorage/UserFolders"
UPLOAD_FILE = "https://api.restorage.io/api/rest/Restorage/UploadFile"
CREATE_FOLDER = "https://api.restorage.io/api/rest/Restorage/CreateFolder"

time = datetime.now()
NOW = time.strftime("%d/%m/%Y%H:%M:%S")

# make dir
if os.path.exists('/opt/restorage'):
    print("starting...")
else:
    os.mkdir('/opt/restorage')
    print('starting...')


@click.group()
def cli():
    pass


@cli.command()
@click.option('--email', prompt='Enter your email', type=str)
def login(email):
    response_send_otp = requests.post(OTP_LOGIN_URL, json={
        'email': email,
    })
    print(response_send_otp.json()['data']['code'])

    if response_send_otp.status_code == 200:
        code = click.prompt("Enter the code you've received", type=int)
        response_auth = requests.post(OTP_AUTH_URL, json={
            'email': email,
            'code': code
        })
        if response_auth.status_code == 200:    
            token = response_auth.json()['data']['token']
            with open('token.txt', 'w') as f:
                f.write(token)
            click.echo(f'Login successful!, Use resotrage --help')
    else:
        click.echo(f'Login failed with status code {response.status_code}.')




@cli.command()
@click.argument('files_array', type=click.Path())
def upload(files_array):
    file = str(os.path.abspath(files_array))
    # folder = click.prompt('Enter your folder name')
    subprocess.run(['cp', file, '/opt/restorage'])
    token = open('token.txt', 'r')
    headers = {'Accept': "Application/json", 'Authorization': 'Bearer ' + token.read()}
    files = {'files[]': open(file, 'rb')}
    # folder_data = {'folder_name': folder}

    user_folders = requests.get(USER_FOLDERS, headers=headers)
    click.echo(click.style('Your folders are listed below',fg='green'))

    for j in user_folders.json()['data']:
        print(j['id'], '-->', j['name'])
    # check if user wants to upload in the existing folder or not
    upload_to_existing = click.prompt(
        click.style("Do you want to upload your file in one of these folders? y|n", fg='green'))

    if upload_to_existing == "y":
        # get the folder id and send request to API
        folder_id = click.prompt(click.style("Enter the id of your folder for your files to be uploaded", fg='green'))
        folder_id_data = {'folder_id': folder_id, 'platform': sys.platform}
        folder_id_request = requests.post(UPLOAD_FILE,
                                          data=folder_id_data,
                                          files=files,
                                          headers=headers)
        if folder_id_request.json()['code'] == 401:
            click.echo(click.style("Your token expired. try `restorage login` and then run your previous command", fg='red'))
        else:
           click.echo("Uploaded successfully. The download link would be email to your account.")


    elif upload_to_existing == "n":
        # create the folder that you want to upload your file
        folder_name = click.prompt(click.style("Enter the folder name that you want to create. It should not be the "
                                               "same name as your folders", fg='green'), type=str)
        folder_name_data = {'name': folder_name}
        # call the api and create the folder
        create_folder = requests.post(CREATE_FOLDER, data=folder_name_data, headers=headers)
        print(create_folder.json()['code'])
        if create_folder.json()['code'] == 401:
            click.echo(click.style("Your token expired. try `restorage login` and then run your previous command", fg='red'))
    else:
        print('else')



@cli.command()
@click.option('--database', prompt='Enter database type (mysql/postgres)', type=click.Choice(['mysql', 'postgres']))
@click.option('--user', prompt='Enter database user', type=str)
@click.option('--password', prompt='Enter database passwrd', type=str)
@click.option('--database_name', prompt='Enter database name', type=str)
@click.option('--file_name', prompt='Enter file name for backup', type=str)
def dump(database, user, password, database_name, file_name):
    cron = click.confirm('Do you want to set this backup as a cron job?')
    if cron:
        minute = click.prompt('Enter the minute (0-59)', type=int)
        hour = click.prompt('Enter the hour (0-23)', type=int)
        day_of_month = click.prompt('Enter the day of the month (1-31)', type=int)
        month = click.prompt('Enter the month (1-12)', type=int)
        day_of_week = click.prompt('Enter the day of the week (0-7)', type=int)
        command = f"{minute} {hour} {day_of_month} {month} {day_of_week} python3 {__file__} dump --database={database} --user={user} --password={password} --database_name={database_name} --file_name={file_name}"
        subprocess.run(f"echo '{command}' >> mycron", shell=True)
        subprocess.run("crontab mycron", shell=True)
        subprocess.run("rm mycron", shell=True)
        click.echo(f'Cron job has been set for database backup.')

    if database == 'mysql':
        FILE_NAME = '/opt/restorage/'+file_name+'.sql'
        subprocess.run(f'mysqldump -u {user} -p {database_name} > {file_name}.sql', shell=True)
        click.echo(f'{database_name} has been backed up successfully to {file_name}.sql')
        
    elif database == 'postgres':
        FILE_NAME = '/opt/restorage/'+file_name+'.tar'
        subprocess.run(f'pg_dump -U {user} -W {database_name} -F t -f {file_name}.tar', shell=True)
        click.echo(f'{database_name} has been backed up successfully to {file_name}.tar')
    
        
    subprocess.run(['cp', f'{file_name}.sql', '/opt/restorage/'])
    token = open('token.txt', 'r')
    headers = {'Accept': "Application/json", 'Authorization': 'Bearer ' + token.read()}
        # upload process
    user_folders = requests.get(USER_FOLDERS, headers=headers)
    click.echo(f'Your folders are listed below')
    for j in user_folders.json()['data']:
        print(j['id'], '-->', j['name'])
    upload_to_existing = click.prompt(
    click.style("Do you want to upload your file in one of these folders? y|n", fg='green'))
    backup_file = {"files[]": open(FILE_NAME, 'rb')}
       
    if upload_to_existing == "y":
        folder_id = click.prompt(click.style("Enter the id of your folder for your files to be uploaded", fg='green'))
        folder_id_data = {'folder_id': folder_id, 'platform': sys.platform}
        folder_id_request = requests.post(UPLOAD_FILE,
                                            data=folder_id_data,
                                            files=backup_file,
                                            headers=headers)
        if folder_id_request.json()['code'] == 401:
            click.echo(click.style("Your token expired. try `restorage login` and then run your previous command", fg='red'))
        elif folder_id_request.json()['code'] == 200:
            click.echo("Uploaded successfully. The download link would be email to your account.")
            if database == "mysql":
                os.remove(f'{file_name}.sql')
            elif database == "postgres":
                os.remove(f'{file_name}.tar')
    elif upload_to_existing == "n":
            click.echo("Creating folder...")
            folder_name = click.prompt(click.style("Enter the folder name", fg='green'))
            create_folder_request = requests.post(CREATE_FOLDER, headers=headers, json={
                "name": folder_name
            })
            # print(create_folder_request.json())
            new_folder_id = {
                "folder_id": create_folder_request.json()['data']['id'],
                "platform": sys.platform
                }
            
            # upload to folder
            upload_to_new_folder = requests.post(UPLOAD_FILE,
                                                 data=new_folder_id,
                                                 files=backup_file,
                                                 headers=headers)
            if upload_to_new_folder.json()['code'] == 200:
                click.echo("Uploaded successfully. The download link would be email to your account.")
                if database == "mysql":
                    os.remove(f'{file_name}.sql')
                elif database == "postgres":
                    os.remove(f'{file_name}.tar')
@cli.command()
@click.option('--database', prompt='Enter database type (mysql/postgres)', type=click.Choice(['mysql', 'postgres']))
@click.option('--user', prompt='Enter database user', type=str)
@click.option('--database_name', prompt='Enter database name', type=str)
@click.option('--file_name', prompt='Enter file name for restore', type=str)
def restore(database, user, database_name, file_name):
    if database == 'mysql':
        subprocess.run(f'mysql -u {user} -p {database_name} < {file_name}.sql', shell=True)
        click.echo(f'{file_name}.sql has been restored to {database_name} successfully.')
    elif database == 'postgres':
        subprocess.run(f'pg_restore -U {user} -W -d {database_name} {file_name}.tar', shell=True)
        click.echo(f'{file_name}.tar has been restored to {database_name} successfully.')





if __name__ == '__main__':
    cli()