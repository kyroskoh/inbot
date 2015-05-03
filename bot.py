from time import sleep

__author__ = 'kotov.a'

import options
import logging
import coloredlogs

logging.basicConfig(level=logging.DEBUG)
coloredlogs.install()


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
    logging.info('Like %s', media_id)
    api.like_media(media_id)


def follow_user(user_id, api):
    logging.info('Follow %s', user_id)
    api.follow_user(user_id=user_id)


def sleep_custom():
    duration = 60
    logging.debug('Sleep %d', duration)
    sleep(duration)


from instagram.client import InstagramAPI

api = InstagramAPI(access_token=options.ACCESS_TOKEN, client_secret=options.CLIENT_SECRET, client_ips="1.2.3.4")

followed_by = get_followed_by(api)
sleep(10)
follow = get_follow(api)
sleep(5)
user_id = api.user().id
logging.info('Start. Followed by %d, follow %d. User id: %s', len(followed_by), len(follow), user_id)
sleep(10)

likes_count = 0
follows_count = 0

ignore_list = []

for tag in options.TAGS:
    logging.debug('Limits %s', api.x_ratelimit_remaining)
    media = list(api.tag_recent_media(tag_name=tag, count=10))

    for m in media[0]:
        media_user_id = m.user.id
        logging.debug('Skip media %s user %s previously followed', m.id, media_user_id)

        if any(x for x in m.likes if x.id == user_id):
            logging.debug('Skip media %s, previously liked', m.id)
            continue

        if any(x for x in follow if x.id == media_user_id):
            logging.debug('Skip media %s, user %s previously followed', m.id, media_user_id)
            continue

        if any(x for x in followed_by if x.id == media_user_id):
            logging.debug('Skip media %s, user %s is follower', m.id, media_user_id)
            continue

        if media_user_id in ignore_list:
            logging.debug('Skip media %s, user %s handled in this session', m.id, media_user_id)
            continue

        if likes_count <= 30:
            sleep_custom()
            like_media(m.id, api)
            likes_count += 1
            ignore_list.append(media_user_id)
            continue
        else:
            logging.warning('Likes limit exceed')

        if follows_count <= 20:
            sleep_custom()
            follow_user(media_user_id, api)
            follows_count += 1
            ignore_list.append(media_user_id)
            continue
        else:
            logging.warning('Follows limit exceed')

        if likes_count >= 30 and follows_count >= 20:
            logging.info('Finish, likes %d, follows %d', likes_count, follows_count)
            exit(0)