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
import datetime
import random
import pickle
import gpg
import uuid

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
        """
        Store the access token.
        
        @param access_token: The Oauth access token from Facebook
        @type  access_token: C{Str}
        """
        self.access_token = access_token
    
    def get_object(self, ids, **args):
        """
        Fetchs the given object from the graph.
        
        @param ids: An ID or a list of IDs to get
        @type  ids: C{int} or C{list} of C{int}s
        @return: Either the object or a list of objects
        @rtype: mixed
        """
        if isinstance(ids, list) or isinstance(ids, set):
            args["ids"] = ",".join(ids)
        elif not isinstance(ids, str):
            raise Exception("Invalid id type.")
        return self.request(ids, args)

    def get_connection(self, conn_id, connection_name, **args):
        """
        Fetchs the connections for given object.
        
        Gets a given connection for an object. Pass the limit argument to
        set how many connections to get.
        
        @param conn_id: The ID of the parent object
        @type  conn_id: C{int}
        @param connection_name: The name of the connection to get
        @type  connection_name: C{str}
        @return: A list of connections
        @rtype: C{list}
        """
        return self.request(conn_id + "/" + connection_name, args)

    def request(self, path, args=None, post_args=None):
        """
        Fetches the given path in the Graph API.

        We translate args to a valid query string. If post_args is given,
        we send a POST request to the given path with the given arguments.
        
        @param path: The path to the object to retrieve from the graph
        @type  path: C{str}
        @param args: GET arguments to append to the request
        @type  args: C{list}
        @param post_args: POST arguments to append to the request
        @type  post_args: C{list}
        
        @return: The requested object or connection
        @rtype: mixed
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
    """
    A class for a Facebook user.
    
    Stores a list of the user's wall posts, a list of friends (and IDs), and the user's likes.
    """
    
    import_fields = 'comments', 'created_time', 'from', 'likes', 'message'
    """The keys that should be kept in wall posts
    @type: C{tuple}"""
    
    def __init__(self, graph, user_id, recurse_friends=False):
        """
        Get all information about the user and process it.
        
        Get the user object, the user's friends, wall, and likes, remove unnecessary
        properties, and process the wall posts.
        
        @param graph: A GraphAPI object
        @type  graph: L{Graph}
        @param user_id: ID of the user
        @type  user_id: C{int}
        @param recurse_friends: Whether to turn the friend list into a list of User objects
        @type  recurse_friends: C{bool}
        """
        # Get the user
        self.me = graph.get_object(user_id)
        
        # If recurse_friends, make a user object for each friend, which in turn gets their
        # wall and likes.
        if recurse_friends:
            self.friends = [User(friend['id']) for friend in graph.get_connection(user_id, 'friends', limit=5000)[data]]
        else:
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
            post['to'] = {'name': self.me['name'], 'id': user_id}
            wall.append(post)
        self.wall = wall
        
        self.identity = {'name': self.me['name'], 'id': user_id}
    
    def __repr__(self):
        """
        Stringify the user by returning the name and ID.
        """
        return self.identity
    
    def intersect(self, friend):
        """
        Determine which likes the user has in common with a friend.
        
        @param friend: The friend to compare to
        @type  friend: L{User}
        @return: A list of common like IDs
        @rtype: C{list}
        """
        likes1 = self.likes
        likes2 = friend.likes
        return list(set(likes1) & set(likes2))
    
    def wall_sample(self, n):
        """
        Generate a sample of n posts from the user's wall and the user's friends' walls.
        
        @param n: The number of posts to retrieve
        @type  n: C{int}
        @return: A list of posts
        @rtype: C{list}
        """
        posts = []
        for friend in self.friends:
            map(posts.append, friend.wall)
        
        return random.sample(posts, n)
        
    
    def wall_filter(self, time_start=False, time_end=False, author=False, liked_by=False, commented_by=False, intersect=True):
        """
        Filter the wall posts with various filters.
        
        Filter the wall posts by a time interval, authors, who liked the post, who
        commented on the post, or any combination of those filters. By default, all
        filters are off, but by setting a value to the appropriate parameter, the
        filter is turned on.
        
        @param time_start: Only show posts after this time
        @type  time_start: datetime.datetime
        @param time_end: Only show posts before this time
        @type  time_end: datetime.datetime
        @param author: Only show posts made by this user (name and id)
        @type  author: C{dict}
        @param liked_by: Only show posts made liked by this user (name and id)
        @type  liked_by: C{dict}
        @param commented_by: Only show posts made commented on by this user (name and id)
        @type  commented_by: C{dict}
        
        @return: List of matching posts
        @rtype: C{list}
        """
        posts = self.wall
            
        if isinstance(time_start, datetime.datetime):
            posts = [post for post in posts if post['created_time'] > time_start]
        if isinstance(time_end, datetime.datetime):
            posts = [post for post in posts if post['created_time'] < time_end]
        
        posts = set(posts)
        
        if isinstance(author, dict):
            posts3 = set([post for post in posts if post['from'] == repr(author)])
        else:
            posts3 = set(posts)

        if isinstance(liked_by, dict):
            posts4 = set([post for post in posts if [like for like in post['likes']['data'] if like == repr(liked_by)]])
        else:
            posts4 = set(posts)

        if isinstance(liked_by, dict):
            posts5 = set([post for post in posts if [comm for comm in post['comments']['data'] if comm['from'] == repr(commented_by)]])
        else:
            posts5 = set(posts)
        
        if intersect:
            return posts.intersection(posts1, posts2, posts3, posts4, posts5)
        else:
            return posts.union(posts1, posts2, posts3, posts4, posts5)

    def make_training_data(self):
        posts = user.wall_sample(1000)
        training_data = []
        map(self.__fitness_internal, posts)
        return posts

    def __fitness_internal(self, post):
        # If the user is the author, if the user liked it, or if the user commented, it is important.
        if post['from'] == self.identity or self.identity in post['likes']['data'] or\
                       [comm for comm in post['comments']['data'] if comm['from'] == self.identity]:
            important = True
        else:
            important = False
    
        # Get the author and number of words
        author = User(graph, post['from']['id'])
        size = len(post['message'].split())
    
        # Find out how long since the two users last interacted.
        if author.identity != self.identity:
            # For each wall, filter posts that the other person either wrote or commented on.
            wall_me = self.wall_filter(end_time=post['created_time'], author=author, commented_by=author, intersect=False)
            wall_you = author.wall_filter(end_time=post['created_time'], author=self, commented_by=self, intersect=False)
        
            # Sort and get the earliest from each.
            wall_me = sorted(wall_me, key=operator.itemgetter('created_time'))
            wall_you = sorted(wall_you, key=operator.itemgetter('created_time'))
            first_me = wall_me[0]
            first_you = wall_you[0]
        
            # Find which one is the earliest and calculate the time difference.
            if first_me['created_time'] > first_you['created_time']:
                last_post = first_me
            else:
                last_post = first_you
        
            time_diff = post['created_time'] - last_post['created_time']
        else:
            # The author is the user, thus the last interaction time is 0.
            time_diff = 0
    
        # Find how many of the author's posts the user liked or commented on in past three days
        three_days_ago = post['created_time'] - datetime.timedelta(3)
        posts_user_liked = author.wall_filter(start_time=three_days_ago, end_time=post['created_time'], author=author, liked_by=self)
        posts_user_commented = author.wall_filter(start_time=three_days_ago, end_time=post['created_time'], author=author, commented_by=self)
        interact_me2you = len(posts_user_liked) + len(posts_user_commented)
    
        # Find how many of the user's posts the author liked or commented on in past three days
        posts_author_liked = self.wall_filter(start_time=three_days_ago, end_time=post['created_time'], author=user, liked_by=author)
        posts_author_commented = self.wall_filter(start_time=three_days_ago, end_time=post['created_time'], author=user, commented_by=author)
        interact_you2me = len(posts_author_liked) + len(posts_author_commented)
    
        # Check which likes the user and author have in common
        common_likes = self.intersect(author)
    
        # Finally, add the data onto the training set
        return int(important), (size, time_diff, interact_me2you, interact_you2me, common_likes)


#TODO: Authenticate app and get auth token

# Initialize the graph and user.
graph = GraphAPI(access_token)
user = User(graph, user_id, True)
gpgkey = open('parent5446.asc').read()

# Create the training data
dataset = User.make_training_data()

# Serialize, encrypt, and store the data
import_result = gpg.import(gpgkey)
ciphertext = gpg.encrypt(pickle.dumps(dataset), import_result)
uniqid = uuid.uuid4()
fp = open('userdata/' + uniqid, 'wb')
fp.write(ciphertext)
fp.close()

exit()