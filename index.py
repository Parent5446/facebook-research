#!/usr/bin/env python
#
# This Facebook SDK is adapted from the official Facebook Graph API Python
# SDK. All original code from that SDK is licensed under the Apache License
# Version 2.0, a copy of which can be found at:
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# All changes, additions, etc. are dually licensed under the Apache License
# Version 2.0 and the GNU General Public License Version 3.0 as indicated below:
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Python client library for the Facebook Platform. This client library is designed to support the
Graph API. Read more about the Graph API at http://developers.facebook.com/docs/api.
"""

from config import APP_ID, APP_URL, APP_SECRET, GPG_HOME

import cgi
import cgitb
import httplib
import logging
import urlparse
import tasks

cgitb.enable()

# Configure logger.
logger = logging.getLogger('facebook-research')
handler = logging.FileHandler('/var/log/facebook-research/access.log')
FORMAT = '%(asctime)s : %(process)d (%(levelname)s) [%(module)s.%(funcName)s] - %(message)s'
formatter = logging.Formatter(FORMAT)
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

logger.info("Facebook Research Data Collection script initiating.")

# Get POST variables
form = cgi.FieldStorage()
authurl1 = "https://www.facebook.com/dialog/oauth?client_id={0}&redirect_uri={1}&scope=user_activities,friends_activities,user_interests,friends_interests,user_likes,friends_likes,user_status,friends_status,email,read_mailbox,read_stream,offline_access"

# Intitiate the session
logger.info("Initiating the session.")
if "code" in form:
    logger.debug("Authentication code found: {0}".format(form['code'].value))
    print "Content-Type: text/html"
    print
elif "error" in form:
    logger.info("App authentication was denied: {0}; {1}".format(form['error_reason'], form['error_description']))
    print "Content-Type: text/plain"
    print
    print "Authentication denied because", form['error_reason']
    logger.info("Script complete.")
    exit()
else:
    logger.info("App not authenticated. Redirecting.")
    print "Location:", authurl1.format(APP_ID, APP_URL)
    print
    logger.info("Script complete.")
    exit()

# Get access token
code = form['code'].value
logger.debug("Opening HTTPS connection with Facebook.")
authconn = httplib.HTTPSConnection('graph.facebook.com')
authurl2 = '/oauth/access_token?client_id={0}&redirect_uri={1}&client_secret={2}&code={3}'
logger.debug("Requesting access token from Facebook.")
authconn.request('GET', authurl2.format(APP_ID, APP_URL, APP_SECRET, code))
response = urlparse.parse_qs(authconn.getresponse().read())
access_token = response['access_token'][0]
logger.info("Access token obtained: {0}".format(access_token))

# Authentication data has been gathered. All further steps can be
# put into a task and set of asynchronously.

tasks.gather_data.delay(access_token)

print """
<!DOCTYPE html>
<html>
    <head>
        <title>SITHS Facebook Research</title>
        <meta charset="utf-8" />
        <style type="text/css">body { text-align: center; }</style>
        
    </head>
    <body>
        <h2>Thank You!</h2>
        <p>You have done all you need to do for this part.
           You may now close this window and browse as you please.</p>
    </body>
</html>
"""
