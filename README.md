# pilot
Alexa application to implement wake-on-lan

I run mine on a Raspberry Pi which is always on.

I have a user pi on the pi.. and run everything from the pilot subdirectory for that user.

I use "runit" to autostart on reboot. The runit config file is in the sv subdirectory.

My process listing post reboot looks something ( exactly ) like this..

```
pi@raspberrypi:~/pilot $ ps -eaf | grep gunicorn
pi         219   216  2 17:09 ?        00:00:09 /usr/bin/python3 /usr/bin/gunicorn3 -c /home/pi/pilot/gunicorn.conf.py --pid=/var/run/pilot/pilot.pid wsgi:app
pi         604   219  1 17:09 ?        00:00:06 /usr/bin/python3 /usr/bin/gunicorn3 -c /home/pi/pilot/gunicorn.conf.py --pid=/var/run/pilot/pilot.pid wsgi:app
pi         605   219  1 17:09 ?        00:00:06 /usr/bin/python3 /usr/bin/gunicorn3 -c /home/pi/pilot/gunicorn.conf.py --pid=/var/run/pilot/pilot.pid wsgi:app
pi         606   219  1 17:09 ?        00:00:06 /usr/bin/python3 /usr/bin/gunicorn3 -c /home/pi/pilot/gunicorn.conf.py --pid=/var/run/pilot/pilot.pid wsgi:app
pi         690   638  0 17:16 pts/0    00:00:00 grep --color=auto gunicorn
```

You need a config file in the pilot subdirectory named config.json.

This is my config file.

```
{
    "applicationId": "amzn1.ask.skill.uuid",
    "hosts": [
        {
            "hostname": "kael",
            "hardwareAddress": "70:71:bc:72:4b:f2"
        }
    ]
}
```

You don't have to add your hostnames into the Alexa app. The pilot does some speech recognition.

I can say...

```
"Alexa, ask pilot to wakeup kael"
"Alexa, ask pilot to suspend kael"
```

For suspend you need to setup remote ssh to the target computer ( mine is running Ubuntu 18.04 ).

I'm only waking/suspending my Plex media server.

At this point.. I don't really recall how I setup the Alexa app :-) as it was over a year ago.

You'll need access to the Alexa Developer Console.

There should be enough screenshots in the Pilot doc for you to mirror the setup.

You need to be running an https server.

I'm using dynu for dynamic DNS, LetsEncrypt for an SSL certificate, and nginx. My anonymised nginx config file is in the nginx sibdirectory.
