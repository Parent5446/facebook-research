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

If your application is using Google AppEngine's webapp framework, your
usage of this module might look like this:

    user = facebook.get_user_from_cookie(self.request.cookies, key, secret)
    if user:
        graph = facebook.GraphAPI(user["access_token"])
        profile = graph.get_object("me")
        friends = graph.get_connections("me", "friends")
"""

import cgi
import hashlib
import time
import urllib

# Find a JSON parser
try:
    import json
    _parse_json = lambda s: json.loads(s)
except ImportError:
    try:
        import simplejson
        _parse_json = lambda s: simplejson.loads(s)
    except ImportError:
        # For Google AppEngine
        from django.utils import simplejson
        _parse_json = lambda s: simplejson.loads(s)


class GraphAPI(object):
    """A client for the Facebook Graph API.

    See http://developers.facebook.com/docs/api for complete documentation
    for the API.

    The Graph API is made up of the objects in Facebook (e.g., people, pages,
    events, photos) and the connections between them (e.g., friends,
    photo tags, and event RSVPs). This client provides access to those
    primitive types in a generic way. For example, given an OAuth access
    token, this will fetch the profile of the active user and the list
    of the user's friends:

       graph = facebook.GraphAPI(access_token)
       user = graph.get_object("me")
       friends = graph.get_connections(user["id"], "friends")

    You can see a list of all of the objects and connections supported
    by the API at http://developers.facebook.com/docs/reference/api/.

    You can obtain an access token via OAuth or by using the Facebook
    JavaScript SDK. See http://developers.facebook.com/docs/authentication/
    for details.

    If you are using the JavaScript SDK, you can use the
    get_user_from_cookie() method below to get the OAuth access token
    for the active user from the cookie saved by the SDK.
    """
    
    def __init__(self, access_token=None):
        self.access_token = access_token

    def get_object(self, id, **args):
        """Fetchs the given object from the graph."""
        return self.request(id, args)

    def get_objects(self, ids, **args):
        """Fetchs all of the given object from the graph.

        We return a map from ID to object. If any of the IDs are invalid,
        we raise an exception.
        """
        args["ids"] = ",".join(ids)
        return self.request("", args)

    def get_connections(self, id, connection_name, **args):
        """Fetchs the connections for given object."""
        return self.request(id + "/" + connection_name, args)

    def put_object(self, parent_object, connection_name, **data):
        """Writes the given object to the graph, connected to the given parent.

        For example,

            graph.put_object("me", "feed", message="Hello, world")

        writes "Hello, world" to the active user's wall. Likewise, this
        will comment on a the first post of the active user's feed:

            feed = graph.get_connections("me", "feed")
            post = feed["data"][0]
            graph.put_object(post["id"], "comments", message="First!")

        See http://developers.facebook.com/docs/api#publishing for all of
        the supported writeable objects.

        Most write operations require extended permissions. For example,
        publishing wall posts requires the "publish_stream" permission. See
        http://developers.facebook.com/docs/authentication/ for details about
        extended permissions.
        """
        assert self.access_token, "Write operations require an access token"
        return self.request(parent_object + "/" + connection_name, post_args=data)

    def put_wall_post(self, message, attachment={}, profile_id="me"):
        """Writes a wall post to the given profile's wall.

        We default to writing to the authenticated user's wall if no
        profile_id is specified.

        attachment adds a structured attachment to the status message being
        posted to the Wall. It should be a dictionary of the form:

            {"name": "Link name"
             "link": "http://www.example.com/",
             "caption": "{*actor*} posted a new review",
             "description": "This is a longer description of the attachment",
             "picture": "http://www.example.com/thumbnail.jpg"}

        """
        return self.put_object(profile_id, "feed", message=message, **attachment)

    def put_comment(self, object_id, message):
        """Writes the given comment on the given post."""
        return self.put_object(object_id, "comments", message=message)

    def put_like(self, object_id):
        """Likes the given post."""
        return self.put_object(object_id, "likes")

    def delete_object(self, id):
        """Deletes the object with the given ID from the graph."""
        self.request(id, post_args={"method": "delete"})

    def request(self, path, args=None, post_args=None):
        """Fetches the given path in the Graph API.

        We translate args to a valid query string. If post_args is given,
        we send a POST request to the given path with the given arguments.
        """
        if not args: args = {}
        if self.access_token:
            if post_args is not None:
                post_args["access_token"] = self.access_token
            else:
                args["access_token"] = self.access_token
        post_data = None if post_args is None else urllib.urlencode(post_args)
        file = urllib.urlopen("https://graph.facebook.com/" + path + "?" +
                              urllib.urlencode(args), post_data)
        try:
            response = _parse_json(file.read())
        finally:
            file.close()
        if response.get("error"):
            raise Error(response["error"]["type"],
                        response["error"]["message"])
        return response
