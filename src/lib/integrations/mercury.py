import logging
from urllib.parse import urlencode

from flask import flash

from bootstrap import conf
from lib.utils import jarr_get
from web.lib.article_cleaner import clean_urls
from web.controllers import ArticleController
from lib.integrations.abstract import AbstractIntegration


logger = logging.getLogger(__name__)
READABILITY_PARSER = 'https://mercury.postlight.com/parser?'


class MercuryIntegration(AbstractIntegration):

    def match_feed_creation(self, *args, **kwargs):
        return False

    def get_article(self, cluster, **kwargs):
        if kwargs.get('article_id'):
            return next(article for article in cluster.articles
                        if article.id == kwargs['article_id'])
        else:
            return cluster.main_article

    def match_article_parsing(self, user, feed, cluster, **kwargs):
        if not kwargs.get('mercury_may_parse'):
            return False
        mercury_available = bool(conf.PLUGINS_READABILITY_KEY or
                                 user.readability_key)
        if not mercury_available:
            return False
        elif self.get_article(cluster, **kwargs).readability_parsed:
            return False
        elif feed.readability_auto_parse:
            return True
        elif kwargs.get('mercury_parse'):
            return True
        return False

    def article_parsing(self, user, feed, cluster, **kwargs):
        article = self.get_article(cluster, **kwargs)
        url = READABILITY_PARSER + urlencode({'url': article.link})
        key = user.readability_key or conf.PLUGINS_READABILITY_KEY
        headers = {'User-Agent': conf.CRAWLER_USER_AGENT, 'x-api-key': key}
        try:
            response = jarr_get(url, headers=headers)
            response.raise_for_status()
            json = response.json()
            if not json:
                raise Exception('Mercury responded with %r(%d)'
                                % (json, response.status_code))
            if 'content' not in json:
                raise Exception('Mercury responded without content')
        except Exception as error:
            flash(error.args[0])
            return article
        artc = ArticleController(user.id)
        new_content = clean_urls(json['content'].replace('&apos;', "'"),
                                 article.link, fix_readability=True)

        artc.update({'id': article.id},
                    {'readability_parsed': True, 'content': new_content})

        article['content'], article['readability_parsed'] = new_content, True
        return article