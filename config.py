import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    def __init__(self):
        self.env_state = os.getenv("ENV_STATE")
        if self.env_state == "dev":
            self.ODOO_URL = os.getenv("DEV_ODOO_URL")
            self.ODOO_CLIENT_ID = os.getenv("DEV_ODOO_CLIENT_ID")
            self.ODOO_CLIENT_SECRET = os.getenv("DEV_ODOO_CLIENT_SECRET")
            self.TOKEN_PATH = os.getenv("DEV_TOKEN_PATH")
            self.SEARCH_PATH = os.getenv("DEV_SEARCH_PATH")
            self.CREATE_PATH = os.getenv("DEV_CREATE_PATH")
        elif self.env_state == "prod":
            self.ODOO_URL = os.getenv("PROD_ODOO_URL")
            self.ODOO_CLIENT_ID = os.getenv("PROD_ODOO_CLIENT_ID")
            self.ODOO_CLIENT_SECRET = os.getenv("PROD_ODOO_CLIENT_SECRET")
            self.TOKEN_PATH = os.getenv("PROD_TOKEN_PATH")
            self.SEARCH_PATH = os.getenv("PROD_SEARCH_PATH")
            self.CREATE_PATH = os.getenv("PROD_CREATE_PATH")
        else:
            raise ValueError("Invalid environment state")

    def __str__(self):
        return f"Config(env_state={self.env_state}, odoo_url={self.ODOO_URL}, odoo_client_id={self.ODOO_CLIENT_ID}, odoo_client_secret={self.ODOO_CLIENT_SECRET}, token_path={self.TOKEN_PATH}, search_path={self.SEARCH_PATH}, create_path={self.CREATE_PATH})"


config = Config()
if __name__ == "__main__":
    print(config)
