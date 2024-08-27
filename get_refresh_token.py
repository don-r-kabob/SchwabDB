#!/usr/bin/env python3
import json
import logging
import os
import sys
import argparse
import schwab
import yaml

import datastructures
from datastructures import Config, read_dashconfig_file


APP_DESCRIPTION = """
This scripts purpose is to obtain an auth token from Schwab. 

1. It will take the information for your app and create a config file to reuse for obtaining an auth token. You
only need to do this once (unless you change your app parameters on schwab's backend)

2. Obtain authorization token by logging into the Schwab site and pasting in the link provided. And create an auth token file

3. Save the token to the cloud (AWS) if specified   

Will check to see if the files created exist
if they do then it will skip the steps.
"""

def read_json_file(file_path):
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)
                return data
        except Exception as e:
            print(f"Error reading JSON file: {e}")
            return None
    else:
        print("File does not exist.")
        return None

def setup_schwab_config(conf: Config, tokenpath, cfile):
    print("Let's setup the configuration!")
    print("What was your APPKEY?: ")
    conf.apikey = input()
    print("What is your app secret?")
    conf.apisecretkey = input()
    print("What is you callback URL?")
    conf.callbackuri = input()
    print("Do you want a default account number? [Leave blank for None, you can add later]")
    def_account = input()
    if def_account is not None and def_account != "":
        conf.defaultAccount = str(def_account)
    conf.tokenpath = tokenpath
    conf.write_config(cfile)


def setup_client(conf: Config):
    client = schwab.auth.client_from_manual_flow(conf.apikey, conf.apisecretkey, conf.callbackuri, conf.tokenpath)
    return client

def __write_to_amazon(appconfig: dict, conf: Config):
    import amazon
    if appconfig.get('app', None).get('aws'):
        try:
            token = conf.tokenpath
            if token:
                amazon.write_token_to_dynamodb(appconfig)
                logging.info("Token saved to AWS")
            else:
                logging.error("Token not found in config.")
        except Exception as e:
            logging.error("failed aws")
def main(
        appconfig={},
        setup=False,
        noauth=False,
        **kwargs
):
    schwab_config_file = appconfig.get('schwab', {}).get('configfile')
    conf: Config
    if noauth is True:
        conf = Config()
        conf.read_config(schwab_config_file)
        __write_to_amazon(appconfig=appconfig, conf=conf)
        return
    if (schwab_config_file and os.path.exists(schwab_config_file) and (setup is False)):
        conf = Config()
        conf.read_config(schwab_config_file)
    elif noauth is False:
        conf = setup_schwab_config()

    client = setup_client(conf=conf)

    if client:
        try:
            account_numbers = client.get_account_numbers().json()
            print("Client setup successful, account numbers retrieved.")
            print(json.dumps(account_numbers, indent=4))
        except Exception as e:
            logging.error(f"Error retrieving account numbers: {e}")
        if appconfig.get('app', None).get('aws'):
            try:
                token = conf.tokenpath
                if token:
                    import amazon
                    amazon.write_token_to_dynamodb(appconfig)
                    logging.info("Token saved to AWS")
                else:
                    logging.error("Token not found in config.")
            except Exception as e:
                logging.error("failed aws")
    else:
        logging.error("Client setup failed.")



if __name__ == '__main__':
    print("Let's get a refresh token")
    ap = argparse.ArgumentParser(
        description=APP_DESCRIPTION
    )
    ap.add_argument(
        "--appconfig",
        dest="appconfig",
        default="dashboard_config.yaml",
        metavar="[dashboard_config.yaml]",
        help="Dashboard configuration file. If no file is found the default script will be copied into the default parameter and used"
    )
    ap.add_argument(
        "--setup",
        dest="setup",
        default=False,
        action="store_true",
        help="Run interactive schwab connection setup. Default is False"
    )
    ap.add_argument(
        "--noauth",
        dest="noauth",
        default=False,
        action="store_true",
        help="Skip authorization step. Result is writing token to cloud and exiting. Default is False "
    )
    args = vars(ap.parse_args())

    #app_config = read_yaml_file(args['appconfig'])
    app_config =  read_dashconfig_file(args['appconfig'])
    main(
        appconfig=app_config,
        setup=args['setup'],
        noauth=args['noauth']
    )
    sys.exit(0)
