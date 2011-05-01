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
from celery.task import task

@task
def add():
    import hashlib
    y = "test"
    for x in range(1, 10000):
        y=y+hashlib.sha1(y).hexdigest()
    open('/var/www/facebook/testdata', 'w').write(y)

@task
def gather_data(access_token):
    # Import modules needed by task
    import gnupg
    import logging
    import uuid
    import pickle
    import facebook
    
    # Configure logger.
    logger = logging.getLogger('facebook-research')
    handler = logging.FileHandler('/var/log/facebook-research/access.log')
    FORMAT = '%(asctime)s : %(process)d (%(levelname)s) [%(module)s.%(funcName)s] - %(message(s)'
    formatter = logging.Formatter(FORMAT)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    
    facebook.find_json(logger)
    
    # Initialize the graph and user.
    logger.debug("Loading Graph API and User objects.")
    graph = facebook.GraphAPI(logger, access_token)
    user = facebook.User(graph, logger, "me", 2)
    gpg = gnupg.GPG(gnupghome=GPG_HOME)
    gpgkey = open('parent5446.asc').read()

    # Create the training data
    logger.debug("Beginning creation of training data.")
    dataset = user.make_training_data()
    logger.debug("Ending creation of training data.")

    # Serialize, encrypt, and store the data
    logger.info("Training data obtained. Beginning encryption.")
    import_result = gpg.import_keys(gpgkey)
    ciphertext = gpg.encrypt(pickle.dumps(dataset), import_result)
    uniqid = uuid.uuid4()
    fp = open('userdata/' + uniqid, 'wb')
    fp.write(ciphertext)
    fp.close()
    logger.info("Script complete.")
