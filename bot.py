from time import sleep

__author__ = 'kotov.a'

import options
import logging
import coloredlogs
import sys

logger = logging.getLogger('inbot')
level = logging.DEBUG
handler = logging.StreamHandler(stream=sys.stdout)
handler.setLevel(level)
logger.addHandler(handler)
coloredlogs.install(level=logging.DEBUG)


def get_followed_by(api):
    followed_by_list = []
    followed_by_generator = api.user_followed_by(as_generator=True, max_pages=300)
    for f in followed_by_generator:
        followed_by_list.extend(f[0])
    return followed_by_list


def get_follow(api):
    follows_list = []
    follows_generator = api.user_follows(as_generator=True, max_pages=300)
    for f in follows_generator:
        follows_list.extend(f[0])
    return follows_list


def like_media(media_id, api):
    logger.info('Like %s', media_id)
    api.like_media(media_id)
    sleep_custom()


def follow_user(user_id, api):
    logger.info('Follow %s', user_id)
    api.follow_user(user_id=user_id)
    sleep_custom()


def sleep_custom():
    duration = 40
    logger.debug('Sleep %d', duration)
    sleep(duration)


from instagram.client import InstagramAPI

api = InstagramAPI(access_token=options.ACCESS_TOKEN, client_secret=options.CLIENT_SECRET, client_ips="1.2.3.4")
logger.debug('Get account information...')
followed_by = get_followed_by(api)
sleep(10)
follow = get_follow(api)
sleep(5)
user_id = api.user().id
logger.info('Start. Followed by %d, follow %d. User id: %s', len(followed_by), len(follow), user_id)
sleep(5)

likes_count = 0
follows_count = 0

ignore_list = []

last_action_is_like = False

try:
    for tag in options.TAGS:
        logger.debug('Limits %s', api.x_ratelimit_remaining)
        media = list(api.tag_recent_media(tag_name=tag, count=20))

        for m in media[0]:
            media_user_id = m.user.id
            logger.debug('Skip media %s user %s previously followed', m.id, media_user_id)

            if any(x for x in m.likes if x.id == user_id):
                logger.debug('Skip media %s, previously liked', m.id)
                continue

            if any(x for x in follow if x.id == media_user_id):
                logger.debug('Skip media %s, user %s previously followed', m.id, media_user_id)
                continue

            if any(x for x in followed_by if x.id == media_user_id):
                logger.debug('Skip media %s, user %s is follower', m.id, media_user_id)
                continue

            if media_user_id in ignore_list:
                logger.debug('Skip media %s, user %s handled in this session', m.id, media_user_id)
                continue

            if not last_action_is_like:
                if likes_count < 30:
                    like_media(m.id, api)
                    likes_count += 1
                    ignore_list.append(media_user_id)
                    last_action_is_like = True
                    continue
                else:
                    logger.warning('Likes limit exceed')

            if last_action_is_like:
                if follows_count < 20:
                    follow_user(media_user_id, api)
                    follows_count += 1
                    ignore_list.append(media_user_id)
                    last_action_is_like = False
                    continue
                else:
                    logger.warning('Follows limit exceed')

        if likes_count >= 30 and follows_count >= 20:
            logger.info('Finish, likes %d, follows %d', likes_count, follows_count)
            exit(0)

except Exception as e:
    logger.exception(e)
finally:
    logger.info('Total, likes: %d, follows: %d', likes_count, follows_count)