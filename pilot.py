import logging

import os
import pwd

from flask import Flask, render_template
from ask_sdk_core.skill_builder import SkillBuilder
from flask_ask_sdk.skill_adapter import SkillAdapter
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model.ui import SimpleCard
from ask_sdk_model import Response

import json

from wakeonlan import send_magic_packet
import paramiko
import socket

import fuzzy


app = Flask(__name__)

if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

passwd = pwd.getpwuid(os.getuid())

with open('config.json', 'r') as config_file:
        config = json.load(config_file)

skill_builder = SkillBuilder()

#app.config['ASK_APPLICATION_ID'] = config['applicationId']

dmeta = fuzzy.DMetaphone()


def match_host(hostname):

    return next((host for host in config['hosts'] if set(list(filter(None.__ne__, dmeta(host['hostname'])))).intersection(list(filter(None.__ne__, dmeta(hostname))))), None)


@skill_builder.request_handler(can_handle_func=is_request_type('LaunchRequest'))
def launch_request_handler(handler_input):
    speech_text = 'This is your pilot speaking. Welcome aboard.'

    return handler_input.response_builder.speak(speech_text).response


@skill_builder.request_handler(can_handle_func=is_intent_name('AMAZON.HelpIntent'))
def help_intent_handler(handler_input):
    speech_text = 'Press the call button if you require a flight attendant.'

    return handler_input.response_builder.speak(speech_text).ask(speech_text).response

@skill_builder.request_handler(can_handle_func=lambda handler_input: is_intent_name('AMAZON.CancelIntent')(handler_input) or is_intent_name('AMAZON.StopIntent')(handler_input))
def cancel_and_stop_intent_handler(handler_input):
    speech_text = 'We hope you enjoyed your flight today. Bon voyage.'

    return handler_input.response_builder.speak(speech_text).set_should_end_session(True).response


@skill_builder.request_handler(can_handle_func=is_intent_name('AMAZON.FallbackIntent'))
def fallback_handler(handler_input):
    speech_text = 'Please remain in your seat with your seatbelt fastened.'

    return handler_input.response_builder.speak(speech_text).ask(speech_text).response


@skill_builder.exception_handler(can_handle_func=lambda i, e: True)
def all_exception_handler(handler_input, exception):
    app.logger.error(exception, exc_info=True)

    speech_text = 'Mayday mayday.'

    handler_input.response_builder.speak(speech_text)

    return handler_input.response_builder.response


@skill_builder.request_handler(can_handle_func=is_intent_name('SuspendIntent'))
def suspend_handler(handler_input):
    request = handler_input.request_envelope.request
    hostname = request.intent.slots['hostname'].value

    host = match_host(hostname)
    if host is not None:
        try:
            client = paramiko.SSHClient()
            client.load_system_host_keys()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            key = paramiko.RSAKey.from_private_key_file(passwd.pw_dir + '/.ssh/id_rsa')

       	    app.logger.info('Shutdown {}'.format(host['hostname']))
            client.connect(host['hostname'], username = passwd.pw_name, pkey = key)

            command = 'sudo systemctl suspend'
            stdin, stdout, stderr = client.exec_command(command)
            app.logger.debug('Command output: {} {}'.format(stdout.read(), stderr.read()))

            speech_text = 'ok'

        except paramiko.ssh_exception.NoValidConnectionsError:
            speech_text = 'ok'

        finally:
            client.close()
    else:
        speech_text = 'Passenger {} is not on the manifest.'.format(hostname)

    return handler_input.response_builder.speak(speech_text).response


@skill_builder.request_handler(can_handle_func=is_intent_name('WakeUpIntent'))
def wakeup_handler(handler_input):
    request = handler_input.request_envelope.request
    hostname = request.intent.slots['hostname'].value

    host = match_host(hostname)
    if host is not None:
        try:
            send_magic_packet(host['hardwareAddress'], ip_address = host['hostname'])
       	    app.logger.info('Send magic packet to {}'.format(host['hardwareAddress']))

       	    speech_text = 'ok'
        except socket.gaierror:
       	    speech_text = 'fail'
    else:
        speech_text = 'Passenger {} is not on the manifest.'.format(hostname)

    return handler_input.response_builder.speak(speech_text).response


@skill_builder.request_handler(can_handle_func=is_request_type('SessionEndedRequest'))
def session_ended_request_handler(handler_input):
    return handler_input.response_builder.response


@skill_builder.global_request_interceptor()
def request_logger(handler_input):
    app.logger.debug('Request received: {}'.format(handler_input.request_envelope.request))


@skill_builder.global_response_interceptor()
def response_logger(handler_input, response):
    app.logger.debug('Response generated: {}'.format(response))


skill_response = SkillAdapter(skill=skill_builder.create(), skill_id=config['applicationId'], app=app)

skill_response.register(app=app, route='/')


if __name__ == '__main__':

    app.run(host = '0.0.0.0', debug = True)

