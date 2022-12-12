import keyring

user_name = input('your username: ')
if keyring.get_password('wheelie', user_name):
    choice = input('your {} password is already stored. do you wish to change it [y/N]? ')
else:
    choice = 'y'

if choice.lower().startswith('y'):
    passwd = input('Please provide new password: ')
    keyring.set_password('wheelie', user_name, passwd)