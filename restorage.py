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
CHECK_TOKEN = "https://api.restorage.io/api/rest/Restorage/UserAccount"

time = datetime.now()
NOW = time.strftime("%d/%m/%Y%H:%M:%S")

# make dir
if os.path.exists('/opt/restorage'):
    pass
else:
    os.mkdir('/opt/restorage')

@click.group()
def cli():
    pass



def check_token(token):
    token = open('/opt/restorage/token.txt', 'r')
    headers = {'Accept': "Application/json", 'Authorization': 'Bearer ' + token.read()}
    # call the check api
    check = requests.get(CHECK_TOKEN, headers=headers)
    if check.json()['code'] == 200:
        return true
        # implement in onther functions
    if check.json()['code'] == 422:
        return False
        print(check.json['errors'])


@cli.command()
@click.option('--email', prompt='Enter your email', type=str)
def login(email):
    response_send_otp = requests.post(OTP_LOGIN_URL, json={
        'email': email,
    })
    # print(response_send_otp.json()['data'])
    if response_send_otp.json()['code'] == 422:
        print(response_send_otp.json()['errors'])
        exit(1)
    if response_send_otp.status_code == 200:
        code = click.prompt("Check your mail inbox. Enter the code you've received", type=int)
        response_auth = requests.post(OTP_AUTH_URL, json={
            'email': email,
            'code': code
        })
        if response_auth.status_code == 200:    
            token = response_auth.json()['data']['token']
            with open('/opt/restorage/token.txt', 'w') as f:
                f.write(token)
            click.echo(f'Login successful!, Use ./resotrage.py --help')
    else:
        click.echo(f'Login failed with status code ' + response_auth.json()['code'])


@cli.command()
@click.argument('directory')
@click.option('--name', prompt='Enter file name', type=str)
def backup_dir(directory, name):
    subprocess.run(['zip', '-r', f'{name}.zip', directory])
    subprocess.run(['cp', f'{name}.zip', '/opt/restorage/'])
    os.remove(f'{name}.zip')
    file_path = '/opt/restorage/'+f'{name}.zip'
    cron = click.confirm('Do you want to set this backup as a cron job?')
    if cron:
        schedule = click.prompt('Enter the cron schedule in the format <minute> <hour> <day_of_month> <month> <day_of_week>', default='0 0 * * *')
        command = f"{schedule} sudo python3 {os.getcwd()}/{__file__} backup-dir {directory}"
        subprocess.run(f"echo '{command}' >> mycron", shell=True)
        subprocess.run("crontab mycron", shell=True)
        subprocess.run("rm mycron", shell=True)
        click.echo(f'Cron job has been set for {directory} backup with schedule "{schedule}".')

    
    token = open('/opt/restorage/token.txt', 'r')
    headers = {'Accept': "Application/json", 'Authorization': 'Bearer ' + token.read()}
    files = {'files[]': open(file_path, 'rb')}

    user_folders = requests.get(USER_FOLDERS, headers=headers)
    if user_folders.json()['data']['folders_count'] >= 1:
            click.echo(click.style('Your folders are listed below',fg='green'))

            for j in user_folders.json()['data']['folders']:
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
                    click.echo(click.style("Your token expired. try `restorage.py login` and then run your previous command", fg='red'))
                else:
                    click.echo("Uploaded successfully. The download link would be email to your account.")


            elif upload_to_existing == "n":
                # create the folder that you want to upload your file
                folder_name = click.prompt(click.style("Enter the folder name that you want to create. It should not be the "
                                                    "same name as your folders", fg='green'), type=str)
                folder_name_data = {'name': folder_name}
                # call the api and create the folder
                create_folder = requests.post(CREATE_FOLDER, data=folder_name_data, headers=headers)
                # if create_folder.json()['code'] == 401:
                #     click.echo(click.style("Your token expired. try `restorage login` and then run your previous command", fg='red'))
                # upload 
                new_folder_data = {
                    "folder_id": create_folder.json()['data']['id'],
                    "platform": sys.platform
                }
                
                upload_new_folder = requests.post(UPLOAD_FILE,
                                                data=new_folder_data,
                                                files=files,
                                                headers=headers)
                if upload_new_folder.json()['code'] == 200:
                    click.echo("Uploaded successfully. The download link would be email to your account.")
                else:
                    raise Exception("error")            
                
    elif user_folders.json()['data']['folders_count'] < 1:
                # create the folder that you want to upload your file
                folder_name = click.prompt(click.style("You don't have any folders, Enter the folder name that you want to create. It should not be the "
                                                    "same name as your other folders", fg='green'), type=str)
                folder_name_data = {'name': folder_name}
                # call the api and create the folder
                create_folder = requests.post(CREATE_FOLDER, data=folder_name_data, headers=headers)
                new_folder_created = {"folder_id": create_folder.json()['data']['id'], "platform":sys.platform}
                # upload
                upload_to_new_folder = requests.post(UPLOAD_FILE,
                                                data=new_folder_created,
                                                files=files,
                                                headers=headers)
                click.echo("Uploaded successfully. The download link would be email to your account.")
                
                if upload_to_new_folder.json()['code'] == 401:
                    click.echo(click.style("Your token expired. try `restorage login` and then run your previous command", fg='red'))
    os.remove('/opt/restorage/'+f'{name}.zip')
    


@cli.command()
@click.argument('file', type=click.Path())
def backup_file(file):
    file = str(os.path.abspath(file))
    subprocess.run(['cp', file, '/opt/restorage'])
    os.remove(f'{name}.zip')
    cron = click.confirm('Do you want to set this backup as a cron job?')
    if cron:
        minute = click.prompt('Enter the minute (0-59)', type=int)
        hour = click.prompt('Enter the hour (0-23)', type=int)
        day_of_month = click.prompt('Enter the day of the month (1-31)', type=int)
        month = click.prompt('Enter the month (1-12)', type=int)
        day_of_week = click.prompt('Enter the day of the week (0-7)', type=int)
        command = f"{minute} {hour} {day_of_month} {month} {day_of_week} sudo python3 f'{os.getcwd()}/{__file__}' backup-file {file}"   
        subprocess.run(f"echo '{command}' >> mycron", shell=True)
        subprocess.run("crontab mycron", shell=True)
        subprocess.run("rm mycron", shell=True)
        click.echo(f'Cron job has been set for {file} backup.')
        

    # folder = click.prompt('Enter your folder name')
    
    token = open('/opt/restorage/token.txt', 'r')
    headers = {'Accept': "Application/json", 'Authorization': 'Bearer ' + token.read()}
    files = {'files[]': open(file, 'rb')}
    # folder_data = {'folder_name': folder}

    user_folders = requests.get(USER_FOLDERS, headers=headers)
    if user_folders.json()['data']['folders_count'] >= 1:
        click.echo(click.style('Your folders are listed below',fg='green'))

        for j in user_folders.json()['data']['folders']:
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
            # print(create_folder.json()['code'])
            if create_folder.json()['code'] == 401:
                click.echo(click.style("Your token expired. try `restorage login` and then run your previous command", fg='red'))
            new_folder_created = {"folder_id": create_folder.json()['data']['id'], "platform":sys.platform}

            upload_to_new_folder = requests.post(UPLOAD_FILE,
                                            data=new_folder_created,
                                            files=files,
                                            headers=headers)
            click.echo("Uploaded successfully. The download link would be email to your account.")
    elif user_folders.json()['data']['folders_count'] < 1:
            # create the folder that you want to upload your file
            folder_name = click.prompt(click.style("You don't have any folders, Enter the folder name that you want to create. It should not be the "
                                                "same name as your other folders", fg='green'), type=str)
            folder_name_data = {'name': folder_name}
            # call the api and create the folder
            create_folder = requests.post(CREATE_FOLDER, data=folder_name_data, headers=headers)
            new_folder_created = {"folder_id": create_folder.json()['data']['id'], "platform":sys.platform}
            # upload
            upload_to_new_folder = requests.post(UPLOAD_FILE,
                                            data=new_folder_created,
                                            files=files,
                                            headers=headers)
            click.echo("Uploaded successfully. The download link would be email to your account.")
            
            if upload_to_new_folder.json()['code'] == 401:
                click.echo(click.style("Your token expired. try `restorage login` and then run your previous command", fg='red'))


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
        command = f"{minute} {hour} {day_of_month} {month} {day_of_week} python3 f'{os.getcwd()}/{__file__}' dump --database={database} --user={user} --password={password} --database_name={database_name} --file_name={file_name}"
        subprocess.run(f"echo '{command}' >> mycron", shell=True)
        subprocess.run("crontab mycron", shell=True)
        subprocess.run("rm mycron", shell=True)
        click.echo(f'Cron job has been set for database backup.')

    if database == 'mysql':
        FILE_NAME = '/opt/restorage/'+file_name+'.sql'
        subprocess.run(f'mysqldump -u {user} -p {database_name} > {file_name}.sql', shell=True)
        click.echo(f'{database_name} has been backed up successfully to {file_name}.sql')
        subprocess.run(['cp', f'{file_name}.sql', '/opt/restorage/'])
        
    elif database == 'postgres':
        FILE_NAME = '/opt/restorage/'+file_name+'.tar'
        subprocess.run(f'pg_dump -U {user} -W {database_name} -F t -f {file_name}.tar', shell=True)
        click.echo(f'{database_name} has been backed up successfully to {file_name}.tar')
        subprocess.run(['cp', f'{file_name}.tar', '/opt/restorage/'])
    
        
    token = open('/opt/restorage/token.txt', 'r')
    headers = {'Accept': "Application/json", 'Authorization': 'Bearer ' + token.read()}
        # upload process
    user_folders = requests.get(USER_FOLDERS, headers=headers)
    
    click.echo(f'Your folders are listed below')
    for j in user_folders.json()['data']['folders']:
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



@cli.command()
def manage_cron():
    print("managing cron")


if __name__ == '__main__':
    cli()
