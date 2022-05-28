from variables import FIRST_NAME, LAST_NAME, USER_NAME, HASHED_PASSWORD, TEAM_NAME, USER_EMAIL


class UserObject:
    def __init__(self, first_name: str = '', last_name: str = '', user_name: str = '', hashed_password: str = '',
                 team_name='', user_email: str = ''):
        self.first_name = first_name
        self.last_name = last_name
        self.user_name = user_name
        self.hashed_password = hashed_password
        self.team_name = team_name
        self.user_email = user_email

    def to_dict(self):
        user_object_dict = {
            FIRST_NAME: self.first_name,
            LAST_NAME: self.last_name,
            USER_NAME: self.user_name,
            HASHED_PASSWORD: self.hashed_password,
            TEAM_NAME: self.team_name,
            USER_EMAIL: self.user_email
        }
        return user_object_dict
