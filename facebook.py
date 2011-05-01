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

APP_ID, APP_URL, APP_SECRET, GPG_HOME = "126673707408216", "http://parent5446.whizkidztech.com/facebook/", "c75102380655cb8dffafc9ac842d735a", "/home/parent5446"

import urllib
import datetime
import random

# Find a JSON parser
def find_json(logger):
    logger.debug("Searching for JSON parser...")
    try:
        import json
        _parse_json = lambda s: json.loads(s)
    except ImportError:
        try:
            import simplejson
            _parse_json = lambda s: simplejson.loads(s)
        except ImportError:
            try:
                # For Google AppEngine
                from django.utils import simplejson
                _parse_json = lambda s: simplejson.loads(s)
            except ImportError:
                logger.critical("JSON parser not found.")
                raise
    finally:
        return _parse_json


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
    
    def __init__(self, logger, json, access_token=None):
        """
        Store the access token.
        
        @param access_token: The Oauth access token from Facebook
        @type  access_token: C{Str}
        """
        self.logger = logger
        self._parse_json = json
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
        elif not isinstance(ids, str) and not isinstance(ids, unicode):
            self.logger.error("Invalid object ID type passed to graph API.")
            raise Exception("Invalid id type {0}.".format(type(ids)))
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

    def request(self, path, args=None):
        """
        Fetches the given path in the Graph API.

        We translate args to a valid query string. If post_args is given,
        we send a POST request to the given path with the given arguments.
        
        @param path: The path to the object to retrieve from the graph
        @type  path: C{str}
        @param args: GET arguments to append to the request
        @type  args: C{list}
        
        @return: The requested object or connection
        @rtype: mixed
        """
        if not args: args = {}
        if self.access_token:
            args["access_token"] = self.access_token
        self.logger.debug("Requesting {0} from Facebook.".format(path))
        self.logger.debug("URL: https://graph.facebook.com/" + path + "?" + urllib.urlencode(args))
        file = urllib.urlopen("https://graph.facebook.com/" + path + "?" + urllib.urlencode(args))
        try:
            response = self._parse_json(file.read())
        finally:
            file.close()
        if response.get("error"):
            self.logger.debug("Error received from Facebook: {0}".format(response["error"]["message"]))
            self.logger.error("Failed to retrieve {0} from Facebook.".format(path))
            raise Exception(response["error"]["type"], response["error"]["message"])
        return response

class User:
    """
    A class for a Facebook user.
    
    Stores a list of the user's wall posts, a list of friends (and IDs), and the user's likes.
    """
    
    import_fields = 'comments', 'created_time', 'from', 'likes', 'message'
    """The keys that should be kept in wall posts
    @type: C{tuple}"""
    
    def __init__(self, graph, logger, user_id, friend_data=1):
        """
        Get all information about the user and process it.
        
        Get the user object, the user's friends, wall, and likes, remove unnecessary
        properties, and process the wall posts.
        
        @param graph: A GraphAPI object
        @type  graph: L{Graph}
        @param user_id: ID of the user
        @type  user_id: C{int}
        @param friend_data: 0 to ignore friends, 1 to get friend list, and 2 to recurse friends
        @type  friend_data: C{int}
        """
        self.logger = logger
        self.logger.info("Retrieving data about user {0}.".format(user_id))
        # Get the user
        self.me = graph.get_object(user_id)
        
        # If recurse_friends, make a user object for each friend, which in turn gets their
        # wall and likes.
        if friend_data == 2:
            self.logger.info("Retrieving friend data from user {0}.".format(user_id))
            self.friends = [User(graph, logger, friend['id'], 0) for friend in graph.get_connection(user_id, 'friends', limit=10)['data']]
        elif friend_data == 1:
            self.logger.debug("Getting friend list from user {0}.".format(user_id))
            self.friends = graph.get_connection(user_id, 'friends', limit=10)['data']
        else:
            self.friends = []
        
        # Get the user's wall and likes. Filter the wall to only get the fields we need
        # and only keep the IDs from the likes
        self.logger.debug("Getting wall data from user {0}.".format(user_id))
        raw_wall = [dict([(key, value) for key, value in post.iteritems() if key in self.import_fields])
                     for post in graph.get_connection(user_id, 'feed', limit=500)['data']]
        self.logger.debug("Getting likes and activities from user {0}.".format(user_id))
        self.likes = [like['id'] for like in graph.get_connection(user_id, 'likes')['data']]
        
        # Convert created_time into datetime
        self.logger.debug("Processing wall posts from user {0}.".format(user_id))
        wall = []
        for post in raw_wall:
            post['created_time'] = datetime.datetime.strptime(post['created_time'][:-5], "%Y-%m-%dT%H:%M:%S")
            post['to'] = {'name': self.me['name'], 'id': user_id}
            wall.append(post)
        self.wall = wall
        
        self.identity = {'name': self.me['name'], 'id': user_id}
    
    def intersect(self, friend):
        """
        Determine which likes the user has in common with a friend.
        
        @param friend: The friend to compare to
        @type  friend: L{User}
        @return: A list of common like IDs
        @rtype: C{list}
        """
        self.logger.debug("Creating likes intersect with user {0} and {1}.".format(self.identity['id'], friend.identity['id']))
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
        self.logger.debug("Generating {0} post wall sample for user {0}.".format(n, self.identity['id']))
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
        # Make user-readable log entry representing this filter.
        logging_string = "Filter wall posts from user {0} for posts with ".format(self.identity['id'])
        if intersect:
            logging_string += "all:"
        else:
            logging_string += "any:"
        if time_start:
            logging_string += " after " + str(time_start) + ";"
        if time_end:
            logging_string += " before " + str(time_end) + ";"
        if author:
            logging_string += " posted by " + author.identity['id'] + ";"
        if liked_by:
            logging_string += " liked by " + liked_by.identity['id'] + ";"
        if commented_by:
            logging_string += " commented by " + commented_by.identity['id'] + ";"
        self.logger.debug(logging_string)
        
        # Start filtering
        posts = self.wall
            
        if isinstance(time_start, datetime.datetime):
            posts = [post for post in posts if post['created_time'] > time_start]
        if isinstance(time_end, datetime.datetime):
            posts = [post for post in posts if post['created_time'] < time_end]
        
        posts = set(posts)
        
        if isinstance(author, User):
            posts3 = set([post for post in posts if post['from'] == author.identity])
        else:
            posts3 = set(posts)

        if isinstance(liked_by, User):
            posts4 = set([post for post in posts if [like for like in post['likes']['data'] if like == liked_by.identity]])
        else:
            posts4 = set(posts)

        if isinstance(liked_by, User):
            posts5 = set([post for post in posts if [comm for comm in post['comments']['data'] if comm['from'] == commented_by.identity]])
        else:
            posts5 = set(posts)
        
        if intersect:
            return posts.intersection(posts1, posts2, posts3, posts4, posts5)
        else:
            return posts.union(posts1, posts2, posts3, posts4, posts5)

    def make_training_data(self):
        """
        Creates a set of training data for the support vector machine.
        
        Creates a sample of posts, uses an internal function to gather data
        from each post, then return the dataset. The length of each post,
        the number of likes the user and author have in common, the time since
        the author and user last communicated, the number of user posts the
        author liked or commented on, and vice-versa are the data that is
        collected.
        
        @return: A list of tuples with an importance indicator and a tuple of data
        @rtype: C{list} of C{tuple} with C{str} and C{tuple}
        """
        posts = self.wall_sample(1000)
        training_data = []
        map(self.__fitness_internal, posts)
        return posts

    def __fitness_internal(self, post):
        """
        Takes an individual post and gathers the necessary data to
        give to the support vector machine.
        
        This is an internal and private function.The length of each post,
        the number of likes the user and author have in common, the time since
        the author and user last communicated, the number of user posts the
        author liked or commented on, and vice-versa are the data that is
        collected.
        
        @param post: A post directly from the Graph API to evaluate
        @return: Whether the post is important and a tuple of parameters
        @rtype: C{tuple} of C{str} and a C{tuple}
        """
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
        posts_author_liked = self.wall_filter(start_time=three_days_ago, end_time=post['created_time'], author=self, liked_by=author)
        posts_author_commented = self.wall_filter(start_time=three_days_ago, end_time=post['created_time'], author=self, commented_by=author)
        interact_you2me = len(posts_author_liked) + len(posts_author_commented)
    
        # Check which likes the user and author have in common
        common_likes = self.intersect(author)
    
        # Finally, add the data onto the training set
        return int(important), (size, time_diff, interact_me2you, interact_you2me, common_likes)
