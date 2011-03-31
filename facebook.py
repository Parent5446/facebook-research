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

# https://www.facebook.com/dialog/oauth?client_id=YOUR_APP_ID&redirect_uri=parent5446.homelinux.com/facebook&scope=user_activities,friends_activities,user_interests,friends_interests,user_likes,friends_likes,user_status,friends_status,email,read_mailbox,read_stream,offline_access

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

    The Graph API is made up of the objects in Facebook (e.g., people, pages,
    events, photos) and the connections between them (e.g., friends,
    photo tags, and event RSVPs).

    You can see a list of all of the objects and connections supported
    by the API at http://developers.facebook.com/docs/reference/api/.

    You can obtain an access token via OAuth. See http://developers.facebook.com/docs/authentication/
    for details.
    """
    
    def __init__(self, access_token=None):
        self.access_token = access_token
    
    def get_object(self, ids, **args):
        """Fetchs the given object from the graph."""
        if isinstance(ids, list) or isinstance(ids, set):
            args["ids"] = ",".join(ids)
        elif not isinstance(ids, str):
            raise Exception("Invalid id type.")
        return self.request(ids, args)

    def get_connection(self, conn_id, connection_name, **args):
        """Fetchs the connections for given object.
        
        Gets a given connection for an object. Pass the limit argument to
        set how many connections to get.
        """
        return self.request(conn_id + "/" + connection_name, args)

    def put_object(self, obj_type, parent_object, message=None):
        """Writes the given object to the graph, connected to the given parent.

        Most write operations require extended permissions. For example,
        publishing wall posts requires the "publish_stream" permission. See
        http://developers.facebook.com/docs/authentication/ for details about
        extended permissions.
        """
        assert self.access_token, "Write operations require an access token"
        if obj_type == "comment":
            connection_name = "comments"
        elif obj_type == "like"
            connection_name = "likes"
        elif obj_type == "wall post":
            connection_name = "feed"
        else:
            raise Exception('Not a common object.')
        return self.request(parent_object + "/" + connection_name, post_args=[message])

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
            raise Exception(response["error"]["type"],
                            response["error"]["message"])
        return response

class User:
    """A class for a Facebook user.
    
    Stores a list of the user's wall posts, a list of friends (and IDs), and the user's likes.
    """
    
    import_fields = 'comments', 'created_time', 'from', 'likes', 'message'
    
    def __init__(self, graph, user_id, recurse_friends=False):
        # Get the user
        self.me = graph.get_object(user_id)
        
        # If recurse_friends, make a user object for each friend, which in turn gets their
        # wall and likes.
        if recurse_friends:
            self.friends = [User(friend['id']) for friend in graph.get_connection(user_id, 'friends', limit=5000)[data]]
        else
            self.friends = graph.get_connection(user_id, 'friends', limit=5000)[data]
        
        # Get the user's wall and likes. Filter the wall to only get the fields we need
        # and only keep the IDs from the likes
        raw_wall = [dict([(key, value) for key, value in post if key in self.import_fields])
                     for post in graph.get_connection(user_id, 'feed', limit=500)[data]]
        self.likes = [like['id'] for like in graph.get_connection(user_id, 'likes')[data]]
        
        # Convert created_time into datetime
        wall = []
        for post in raw_wall:
            year, month, day, hour, minute, second, tzinfo = post['created_time'].split('-T:+')
            post['created_time'] = datetime.datetime(year, month, day, hour, minute, second)
            wall.append(post)
        self.wall = wall
    
    def intersect(self, friend):
        likes1 = self.likes
        likes2 = friend.likes
        return list(set(likes1) & set(likes2))
    
    def filter_wall(self, time_start=False, time_end=False, author=False, liked_by=False, commented_by=False):
        posts = self.wall
        
        if isinstance(time_start, datetime.datetime):
            posts = [post for post in posts if post['created_time'] > time_start]
        if isinstance(time_end, datetime.datetime):
            posts = [post for post in posts if post['created_time'] < time_end]
        
        if isinstance(author, int):
            posts = [post for post in posts if post['from']['id'] == author]
        elif isinstance(author, str):
            posts = [post for post in posts if post['from']['name'] == author]

        if isinstance(liked_by, int):
            posts = [post for post in posts if [like for like in post['likes']['data'] if like['id'] == liked_by]]
        elif isinstance(author, str):
            posts = [post for post in posts if [like for like in post['likes']['data'] if like['name'] == liked_by]]

        if isinstance(liked_by, int):
            posts = [post for post in posts if [comm for comm in post['comments']['data'] if comm['from']['id'] == commented_by]]
        elif isinstance(author, str):
            posts = [post for post in posts if [comm for comm in post['comments']['data'] if comm['from']['name'] == commented_by]]
        
        return posts


# Process:
# 1) Get list of friends (me/friends)
# 2) Get the walls of the user and all friends (<friend>/feed)
# 3) For each post, if a dict with the user's name, id is in the 'from' key or in the 'data' key of
#    either the 'comments' or 'likes' key, then it is important. Otherwise, unimportant.
# 4) Get the size of the post in words
# 5) Check the user's wall and author's wall for the last interaction
#       * Get <friend>/feed and me/feed
#       * Filter only posts with 'created_time' key before the test post being analyzed
#       * For each wall go through each post:
#           * If the friend's wall, did the user post it?
#           * If the user's wall, did the author post it?
#           * If the friend's wall, is a dict with user's name, id in the 'data' key of the 'comments' key?
#           * If the user's wall, is a dict with author's name, id in the 'data' key of the 'comments' key?
#       * Get the first post in each wall that satifies *one* of those conditions.
#       * Compare timestamps under 'created_time' and see which was first
#       * Calculate the time difference between this post and the post being analyzed
# 6) Check the author's wall for all posts the user liked or commented on in past three days
#       * Get <friend>/feed
#       * Take result['data'] and filter only posts in past three days
#       * Filter only posts whose 'from' key has a dictionary with the name, id of author
#       * Check the value of 'data' key under the 'likes' key and check for a dict with name, id of user
#       * Check the value of 'data' key under the 'comments' key and check for a dict with name, id of user
#       * Count the number of posts
# 7) Check the user's wall for all posts author liked or commented on in past three day
#       * Get me/feed
#       * Take result['data'] and filter only posts in past three days
#       * Filter only posts whose 'from' key has a dictionary with the name, id of user
#       * Check the value of 'data' key under the 'likes' key and check for a dict with name, id of author
#       * Check the value of 'data' key under the 'comments' key and check for a dict with name, id of author
#       * Count the number of posts
# 8) Check which likes the user and author have in common
#       * Get me/likes and <friend>/likes
#       * Take result['data']
#       * Make a list of the 'id' values for each dictionary in the list
#       * Go through the user's likes and find a correlating author's like
#       * Count the number of common likes

#TODO: Authenticate app and get auth token

