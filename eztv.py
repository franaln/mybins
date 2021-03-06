#! /usr/bin/env python2.7

import sys
import argparse
from bs4 import BeautifulSoup
import requests
import re

URL = "https://eztv.ag"
QUALITY_PREF = "720p"
#QUALITY_PREF = "1080p"

class EztvAPI(object):
    """
        EztvAPI Main Handler
    """

    _instance = None
    _id_tv_show = None
    _season_and_episode = {}
    _patterns = [
        r"S(\d+)E(\d+)",  # Matches SXXEYY (eg. S01E10)
        r"(\d+)x(\d+)",   # Matches SSxYY (eg. 01x10)
    ]

    def __new__(cls, *args, **kwargs):
        """
            __new__ builtin
        """
        if not cls._instance:
            cls._instance = super(EztvAPI, cls).__new__(
                cls, *args, **kwargs)
        return cls._instance

    def _match_pattern(self, pattern, episode):
        regex = re.search(pattern, episode)
        if regex is None:  # Yeah, I try to be a positive person.
            return

        season_tv_show = regex.group(1)
        episode_tv_show = regex.group(2)
        regex = re.search(r"href=\"(.*)\" ", episode)
        magnet_link = regex.group(1)

        return (season_tv_show, episode_tv_show, magnet_link.split('"')[0])

    def tv_show(self, name):
        """
            Fetches a show mapping $name returns a $self instance.
            Might raise a TVShowNotFound exception
        """
        # all strings are in lowercase
        name = name.lower()

        url = URL + '/search/' + name
        self.content = requests.get(url, timeout=5).content

        # load the tv show data
        self.load_tv_show_data()
        return self._instance

    def load_tv_show_data(self):
        """
            load the data, create a dictionary structure with all seasons,
            episodes, magnet.
        """
        soup = BeautifulSoup(self.content, 'html.parser')

        self._season_and_episode = {}
        episodes = str(soup('a', {'class': 'magnet'})).split('</a>')

        for epi in episodes:
            for pat in self._patterns:
                data = self._match_pattern(pat, epi)
                if data is None:
                    continue

                name = re.findall('title="(.*)"', epi)[0]
                self.add_season_and_episode(name, data[0], data[1], data[2])

        return self._instance

    def add_season_and_episode(self, name, num_season, num_episode, magnet_link):
        """
             insert into the dictionary the season and the episode with the
             specific magnet link
             but also consider quality preference (QUALITY_PREF)
        """
        num_season = int(num_season)
        num_episode = int(num_episode)
        magnet_link = magnet_link.replace('&amp;', '&')

        name = name.replace(' Magnet Link', '')

        if (num_season not in self._season_and_episode):
            self._season_and_episode[num_season] = {}

        if (num_episode not in self._season_and_episode[num_season] and QUALITY_PREF in magnet_link):
            self._season_and_episode[num_season][num_episode] = [(name, magnet_link),]
        elif (QUALITY_PREF in magnet_link):
            self._season_and_episode[num_season][num_episode].append((name, magnet_link))

        return self._instance

    def episode(self, num_season=None, num_episode=None):
        """
             specific episode
             return magnet link of episode
             might raise SeasonNotFound or EpisodeNotFound exceptions
        """
        # specific episode
        if (num_season is not None and num_episode is not None):
            # verifiyng the season exist
            if (num_season not in self._season_and_episode):
                raise # SeasonNotFound(
                    # 'The season %s does not exist.' % num_season, None)

            # verifying the episode exists
            if (num_episode not in self._season_and_episode[num_season]):
                raise # deNotFound(
                    # 'The episode %s does not exist.' % num_episode, None)

            return self._season_and_episode[num_season][num_episode]

    def season(self, num_season=None):
        """
             specifc season
             return data structure (dictionary)
             might raise SeasonNotFound exceptions
        """
        # specific season, all episodes
        if (num_season is not None):
            # verifiyng the season exist
            if (num_season not in self._season_and_episode):
                raise SeasonNotFound(
                    'The season %s does not exist.' % num_season, None)

            return self._season_and_episode[num_season]

        # all seasons
        else:
            return self._season_and_episode

    def seasons(self):
        """
            all seasons
        """
        return self._season_and_episode

    def update(self):
        """
            load the data, create a dictionary structure with all seasons,
            episodes, magnet.
        """
        return self.load_tv_show_data()

    def __iter__(self):
        for season, episodes_dict in self._season_and_episode.iteritems():
            for episode, (name, magnet) in episodes_dict.iteritems():
                yield (name, magnet)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='')

    parser.add_argument('-n', dest='series_name', help='Series name')
    parser.add_argument('-s', dest='season', type=int, help='Season')
    parser.add_argument('-e', dest='episode', type=int, help='Episode')
    parser.add_argument('-q', dest='quality', help='Quality')


    args = parser.parse_args()

    if args.series_name is None:
        parser.print_help()
        sys.exit(1)


    eps = EztvAPI().tv_show(args.series_name)

    if args.season is not None and args.episode is not None:

        list_ = eps.episode(args.season, args.episode)

        for (name, link) in list_:
            print(name)
            print(link)

    elif args.season is not None:

        d = eps.season(args.season)

        for n, (name, magnet) in d.items():
            print name
            print magnet
            print ' '

    else:
        for name, magnet in eps:
            print name
            print magnet
            print ' '
