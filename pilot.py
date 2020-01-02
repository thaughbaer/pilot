import logging

import os
import pwd

from flask import Flask, render_template

from flask_ask import Ask, statement, question, session, context

import json

import paramiko

from wakeonlan import send_magic_packet

import fuzzy

logger = logging.getLogger("flask_ask")
logger.setLevel(logging.DEBUG)

passwd = pwd.getpwuid(os.getuid())

with open('config.json', 'r') as config_file:
        config = json.load(config_file)

app = Flask(__name__)

ask = Ask(app, "/")

app.config['ASK_APPLICATION_ID'] = config['applicationId']

dmeta = fuzzy.DMetaphone()


def match_host(hostname):

    return next((host for host in config['hosts'] if set(list(filter(None.__ne__, dmeta(host['hostname'])))).intersection(list(filter(None.__ne__, dmeta(hostname))))), None)


@ask.launch
def launch():

    return_msg = render_template('welcome_aboard')

    return question(return_msg)


@ask.intent('AMAZON.FallbackIntent')
def fallback():
    return_msg = render_template('safety_briefing')

    return question(return_msg)


@ask.intent('AMAZON.HelpIntent')
def help():
    return_msg = render_template('safety_briefing')

    return question(return_msg)


@ask.intent('AMAZON.StopIntent')
def stop():
    return_msg = render_template('bon_voyage')

    return question(return_msg)


@ask.intent('AMAZON.CancelIntent')
def cancel():
    return_msg = render_template('bon_voyage')

    return question(return_msg)


@ask.session_ended
def session_ended():
    return "{}", 200


@ask.intent("SuspendIntent", convert = {'hostname': str})
def suspend(hostname):

    host = match_host(hostname)
    if host is not None:
        try:
            client = paramiko.SSHClient()
            client.load_system_host_keys()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            key = paramiko.RSAKey.from_private_key_file(passwd.pw_dir + '/.ssh/id_rsa')

            client.connect(host['hostname'], username = passwd.pw_name, pkey = key)

            command = "sudo systemctl suspend"
            stdin, stdout, stderr = client.exec_command(command)
            print(stdout.read())

        except paramiko.ssh_exception.NoValidConnectionsError:
            pass

        finally:
            client.close()

        return_msg = render_template('ok')

    else:
        return_msg = render_template('unknown_hostname', hostname = hostname)

    return statement(return_msg)


@ask.intent("WakeUpIntent", convert = {'hostname': str})
def wake_up(hostname):

    host = match_host(hostname)
    if host is not None:
        send_magic_packet(host['hardwareAddress'], ip_address = host['hostname'])
        logger.debug("Send magic packet to {}".format(host['hardwareAddress']))
        return_msg = render_template('ok')
    else:
        return_msg = render_template('unknown_hostname', hostname = hostname)

    return statement(return_msg)


if __name__ == '__main__':

    app.run(host = '0.0.0.0', debug = True)

