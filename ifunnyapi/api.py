"""Unofficial wrapper for iFunny's private API

Example:

from ifunnyapi.api import IFAPI
api = IFAPI("token")
for post in api.user_posts(user_id=api.account["id"]):
    api.smile_post(post_id=post["id"])
for feat in api.featured(limit=1):
    api.comment("nice feature!", post_id=feat["id"])
"""

import io
import json
from typing import Generator, List, Union

from PIL import Image, UnidentifiedImageError
import requests

from .auth import AuthBearer
from .endpoints import (
    BASE,
    ACCOUNT,
    REVOKE,
    USERS,
    POSTS,
    COMMENTS,
    CHANNELS,
    MY_ACTIVITY,
    MY_BLOCKED_USERS,
    MY_COMMENTS,
    USER_SUBSCRIBERS,
    USER_SUBSCRIPTIONS,
    USER_POSTS,
    USER_FEATURES,
    USER_GUESTS,
    CHANNEL_POSTS,
    SEARCH_POSTS,
    POST_COMMENTS,
    POST_SMILES_USERS,
    POST_REPUBS_USERS,
    COMMENT_REPLIES,
    READS,
    FEATURED_FEED,
    COLLECTIVE_FEED,
    SUBSCRIPTIONS_FEED,
    POPULAR_FEED,
    DIGEST_POSTS,
    UPLOAD,
    BLOCK_USER,
    REPORT_USER,
    REPORT_POST,
    REPORT_COMMENT,
    PIN_POST,
    REPUBLISH_POST,
    SMILE_POST,
    UNSMILE_POST,
    SMILE_COMMENT,
    UNSMILE_COMMENT,
    USER_BY_NICK,
    IS_NICK_AVAILABLE,
    IS_EMAIL_AVAILABLE
)
from .enums import IFChannel, IFPostVisibility, IFReportType
from .utils import api_request


class _IFBaseAPI:
    """Private API class, only interacts with iFunny API endpoints"""

    def __init__(self, token: str):
        self.token = token
        self.auth = AuthBearer(self.token)

    @api_request
    def _get(self, path: str, **kwargs) -> dict:
        """GET request with authorization.

        Args:
            path: iFunny API endpoint path.
            **kwargs: Arbitrary keyword arguments passed to request.

        Returns:
            JSON dictionary of request output.
        """

        req = requests.get(BASE + path, auth=self.auth, **kwargs)
        return req.json()

    @api_request
    def _post(self, path: str, **kwargs) -> dict:
        """POST request with authorization.

        Args:
            path: iFunny API endpoint path.
            **kwargs: Arbitrary keyword arguments passed to request.

        Returns:
            JSON dictionary of request output.
        """

        req = requests.post(BASE + path, auth=self.auth, **kwargs)
        return req.json()

    @api_request
    def _put(self, path: str, **kwargs) -> dict:
        """PUT request with authorization.

        Args:
            path: iFunny API endpoint path.
            **kwargs: Arbitrary keyword arguments passed to request.

        Returns:
            JSON dictionary of request output.
        """

        req = requests.put(BASE + path, auth=self.auth, **kwargs)
        return req.json()

    @api_request
    def _delete(self, path: str, **kwargs) -> dict:
        """DELETE request with authorization.

        Args:
            path: iFunny API endpoint path.
            **kwargs: Arbitrary keyword arguments passed to request.

        Returns:
            JSON dictionary of request output.
        """

        req = requests.delete(BASE + path, auth=self.auth, **kwargs)
        return req.json()

    def revoke(self, **kwargs):
        """Revoke the iFunny bearer token in use.

        Args:
            **kwargs: Arbitrary keyword arguments passed to requests.
        """

        self._post(REVOKE, data={"token": self.token}, **kwargs)

    @property
    def account(self, **kwargs) -> dict:
        """Retrieve iFunny account tied to authorization token.

        Args:
            **kwargs: Arbitrary keyword arguments passed to requests.

        Returns:
            JSON dictionary of iFunny account.
        """

        return self._get(ACCOUNT, **kwargs)["data"]

    def user_info(self, *, user_id: str, **kwargs) -> dict:
        """Retrieve iFunny user.

        Args:
            user_id: iFunny ID of user to retrieve.
            **kwargs: Arbitrary keyword arguments passed to requests.

        Returns:
            JSON dictionary of iFunny user.
        """

        return self._get(USERS.format(user_id), **kwargs)["data"]

    def post_info(self, *, post_id: str, **kwargs) -> dict:
        """Retrieve iFunny post.

        Args:
            post_id: iFunny ID of post to retrieve.
            **kwargs: Arbitrary keyword arguments passed to requests.

        Returns:
            JSON dictionary of iFunny post.
        """

        return self._get(POSTS.format(post_id), **kwargs)["data"]

    def comment_info(self, *, post_id: str, comment_id: str, **kwargs) -> dict:
        """Retrieve iFunny comment.

        Args:
            post_id: iFunny ID of post with comment to retrieve.
            comment_id: iFunny ID of comment to retrieve.
            **kwargs: Arbitrary keyword arguments passed to requests.

        Returns:
            JSON dictionary of iFunny comment.
        """

        return self._get(COMMENTS.format(post_id, comment_id), **kwargs)["data"]

    def channels_info(self, **kwargs) -> List[dict]:
        """Retrieve iFunny channels.

        Args:
            **kwargs: Arbitrary keyword arguments passed to requests.

        Returns:
            List of JSON dictionary of iFunny channels.
        """

        return self._get(CHANNELS, **kwargs)["data"]["channels"]["items"]

    def _get_paging_items(self, path: str, key: str, limit: int = None, **kwargs) -> List[dict]:
        """Retrieve paging content from iFunny API.

        Args:
            path: iFunny API endpoint path.
            key: Response JSON dictionary key that contains requested paging
                items.
            limit: Number of paging items to retrieve.
            **kwargs: Arbitrary keyword arguments passed to requests.

        Returns:
            List of JSON dictionaries of paging items.
        """

        def get_next(jso: dict) -> int:
            return jso["data"][key]["paging"]["cursors"]["next"]

        def has_next(jso: dict) -> bool:
            return jso["data"][key]["paging"]["hasNext"]

        def get_items(jso: dict) -> list:
            return jso["data"][key]["items"]

        lnone = limit is None
        ilim = 100 if lnone or limit > 100 else limit
        val = rem = 0
        batch = self._get(path, params={"limit": ilim}, **kwargs)
        items = get_items(batch)

        if not lnone and limit <= 100:
            return items
        if not lnone:
            val, rem = divmod(limit - 100, 100)
        lbuffer = 0  # Significant only when limit is not None

        while has_next(batch) if lnone else lbuffer in range(val):
            lbuffer += 1
            batch = self._get(path, params={"limit": 100, "next": get_next(batch)}, **kwargs)
            items.extend(get_items(batch))
        if lnone:
            batch = self._get(path, params={"limit": 100, "next": get_next(batch)}, **kwargs)
        else:
            batch = self._get(path, params={"limit": rem}, **kwargs)
        items.extend(get_items(batch))
        return items

    def my_activity(self, limit: int = None, **kwargs) -> List[dict]:
        """Retrieve iFunny account activity.

        Args:
            limit: Number of activity items to retrieve.
            **kwargs: Arbitrary keyword arguments passed to requests.

        Returns:
            List of JSON dictionaries of iFunny account activity.
        """

        return self._get_paging_items(MY_ACTIVITY, "news", limit, **kwargs)

    def my_comments(self, limit: int = None, **kwargs) -> List[dict]:
        """Retrieve iFunny account comments.

        Args:
            limit: Number of comments to retrieve.
            **kwargs: Arbitrary keyword arguments passed to requests.

        Returns:
            List of JSON dictionaries of iFunny account comments.
        """

        return self._get_paging_items(MY_COMMENTS, "comments", limit, **kwargs)

    def my_blocked_users(self, limit: int = None, **kwargs) -> List[dict]:
        """Retrieve iFunny blocked users.

        Args:
            limit: Number of users to retrieve.
            **kwargs: Arbitrary keyword arguments passed to requests.

        Returns:
            List of JSON dictionaries of iFunny blocked users.
        """

        return self._get_paging_items(MY_BLOCKED_USERS, "users", limit, **kwargs)

    def user_subscribers(self, *, user_id: str, limit: int = None, **kwargs) -> List[dict]:
        """Retrieve iFunny user subscribers.

        Args:
            user_id: iFunny ID of user from which to retrieve subscribers.
            limit: Number of subscribers to retrieve.
            **kwargs: Arbitrary keyword arguments passed to requests.

        Returns:
            List of JSON dictionaries of iFunny user subscribers.
        """

        return self._get_paging_items(USER_SUBSCRIBERS.format(user_id), "users", limit, **kwargs)

    def user_subscriptions(self, *, user_id: str, limit: int = None, **kwargs) -> List[dict]:
        """Retrieve iFunny user subscriptions.

        Args:
            user_id: iFunny ID of user from which to retrieve subscriptions.
            limit: Number of subscriptions to retrieve.
            **kwargs: Arbitrary keyword arguments passed to requests.

        Returns:
            List of JSON dictionaries of iFunny user subscriptions.
        """

        return self._get_paging_items(USER_SUBSCRIPTIONS.format(user_id), "users", limit, **kwargs)

    def user_posts(self, *, user_id: str, limit: int = None, **kwargs) -> List[dict]:
        """Retrieve iFunny user posts.

        Args:
            user_id: iFunny ID of user from which to retrieve posts.
            limit: Number of posts to retrieve.
            **kwargs: Arbitrary keyword arguments passed to requests.

        Returns:
            List of JSON dictionaries of iFunny user posts.
        """

        return self._get_paging_items(USER_POSTS.format(user_id), "content", limit, **kwargs)

    def user_features(self, *, user_id: str, limit: int = None, **kwargs) -> List[dict]:
        """Retrieve iFunny user features.

        Args:
            user_id: iFunny ID of user from which to retrieve features.
            limit: Number of features to retrieve.
            **kwargs: Arbitrary keyword arguments passed to requests.

        Returns:
            List of JSON dictionaries of iFunny user features.
        """

        return self._get_paging_items(USER_FEATURES.format(user_id), "content", limit, **kwargs)

    def user_guests(self, *, user_id: str, limit: int = None, **kwargs) -> List[dict]:
        """Retrieve iFunny user guests.

        Args:
            user_id: iFunny ID of user from which to retrieve guests.
            limit: Number of guests to retrieve.
            **kwargs: Arbitrary keyword arguments passed to requests.

        Returns:
            List of JSON dictionaries of iFunny user guests.
        """

        return self._get_paging_items(USER_GUESTS.format(user_id), "guests", limit, **kwargs)

    def channel_posts(self, *, channel: IFChannel, limit: int = None, **kwargs) -> List[dict]:
        """Retrieve iFunny posts from specified channel.

        Args:
            channel: Channel of iFunny posts.
            limit: Number of posts to retrieve.
            **kwargs: Arbitrary keyword arguments passed to requests.

        Returns:
            List of JSON dictionaries of iFunny posts from specified channel.
        """

        return self._get_paging_items(CHANNEL_POSTS.format(channel.value), "content", limit, **kwargs)

    def tag_posts(self, *, tag: str, limit: int = None, **kwargs) -> List[dict]:
        """Retrieve iFunny posts with specified hashtag.

        Args:
            tag: Hashtag of iFunny posts.
            limit: Number of posts to retrieve.
            **kwargs: Arbitrary keyword arguments passed to requests.

        Returns:
            List of JSON dictionaries of iFunny posts with specified hashtag.
        """

        return self._get_paging_items(SEARCH_POSTS, "content",
                                      limit, params={"counters": "content", "tag": tag}, **kwargs)

    def post_comments(self, *, post_id: str, limit: int = None, **kwargs) -> List[dict]:
        """Retrieve iFunny comments on specified post.

        Args:
            post_id: iFunny ID of post from which to retrieve comments.
            limit: Number of comments to retrieve.
            **kwargs: Arbitrary keyword arguments passed to requests.

        Returns:
            List of JSON dictionaries of iFunny comments on specified post.
        """

        return self._get_paging_items(POST_COMMENTS.format(post_id), "comments", limit, **kwargs)

    def post_smiles_users(self, *, post_id: str, limit: int = None, **kwargs) -> List[dict]:
        """Retrieve iFunny users that smiled specified post.

        Args:
            post_id: iFunny ID of post from which to retrieve smilers.
            limit: Number of smilers to retrieve.
            **kwargs: Arbitrary keyword arguments passed to requests.

        Returns:
            List of JSON dictionaries of iFunny users that smiled specified
            post.
        """

        return self._get_paging_items(POST_SMILES_USERS.format(post_id), "users", limit, **kwargs)

    def post_repubs_users(self, *, post_id: str, limit: int = None, **kwargs) -> List[dict]:
        """Retrieve iFunny users that republished specified post.

        Args:
            post_id: iFunny ID of post from which to retrieve republishers.
            limit: Number of republishers to retrieve.
            **kwargs: Arbitrary keyword arguments passed to requests.

        Returns:
            List of JSON dictionaries of iFunny users that republished
            specified post.
        """

        return self._get_paging_items(POST_REPUBS_USERS.format(post_id), "users", limit, **kwargs)

    def comment_replies(self, *, post_id: str, comment_id: str, limit: int = None, **kwargs) -> List[dict]:
        """Retrieve iFunny replies to specified comment.

        Args:
            post_id: iFunny ID of post from which to retrieve replies to
                specified comment.
            comment_id: iFunny ID of comment with replies.
            limit: Number of replies to retrieve.
            **kwargs: Arbitrary keyword arguments passed to requests.

        Returns:
            List of JSON dictionaries of iFunny replies to specified comment.
        """

        return self._get_paging_items(COMMENT_REPLIES.format(post_id, comment_id), "replies", limit, **kwargs)

    def featured(self, limit: int = None, read: bool = True, **kwargs) -> Generator[dict, None, None]:
        """Retrieve iFunny featured posts.

        Args:
            limit: Number of featured posts to retrieve.
            read: Option to send iFunny read request. If toggled False, iFunny
                will repeatedly send the same featured post.
            **kwargs: Arbitrary keyword arguments passed to requests.

        Returns:
            Generator of JSON dictionaries of iFunny featured posts.
        """

        iterator = iter(int, 1) if limit is None else range(limit)
        for _ in iterator:
            jso = self._get(FEATURED_FEED, params={"limit": 1}, **kwargs)
            feat = jso["data"]["content"]["items"][0]
            if read:
                self._put(READS.format(feat["id"]), params={"from": "feat"}, headers={"User-Agent": "*"})
            yield feat

    def collective(self, limit: int = None, **kwargs) -> Generator[dict, None, None]:
        """Retrieve iFunny collective posts.

        Args:
            limit: Number of collective posts to retrieve.
            **kwargs: Arbitrary keyword arguments passed to requests.

        Returns:
            Generator of JSON dictionaries of iFunny collective posts.
        """

        iterator = iter(int, 1) if limit is None else range(limit)
        for _ in iterator:
            jso = self._post(COLLECTIVE_FEED, params={"limit": 1}, **kwargs)
            coll = jso["data"]["content"]["items"][0]
            yield coll

    def subscriptions(self, limit: int = None, read: bool = True, **kwargs) -> Generator[dict, None, None]:
        """Retrieve iFunny subscriptions posts.

        Args:
            limit: Number of subscriptions posts to retrieve.
            read: Option to send iFunny read request. If toggled False, iFunny
                will repeatedly send the same subscriptions post.
            **kwargs: Arbitrary keyword arguments passed to requests.

        Returns:
            Generator of JSON dictionaries of iFunny subscriptions posts.
        """

        iterator = iter(int, 1) if limit is None else range(limit)
        for _ in iterator:
            jso = self._get(SUBSCRIPTIONS_FEED, params={"limit": 1}, **kwargs)
            subscr = jso["data"]["content"]["items"][0]
            if read:
                self._put(READS.format(subscr["id"]), params={"from": "subs"}, headers={"User-Agent": "*"})
            yield subscr

    def popular(self, limit: int = None, **kwargs) -> Generator[dict, None, None]:
        """Retrieve iFunny popular posts.

        Args:
            limit: Number of popular posts to retrieve.
            **kwargs: Arbitrary keyword arguments passed to requests.

        Returns:
            Generator of JSON dictionaries of iFunny popular posts.
        """

        iterator = iter(int, 1) if limit is None else range(limit)
        for _ in iterator:
            jso = self._get(POPULAR_FEED, params={"limit": 1}, **kwargs)
            pop = jso["data"]["content"]["items"][0]
            yield pop

    def digest_posts(self, *, day: int, month: int, year: int, **kwargs) -> List[dict]:
        """Retrieve iFunny posts from specified digest.

        Args:
            day: Digest day.
            month: Digest month.
            year: Digest year.
            **kwargs: Arbitrary keyword arguments passed to requests.

        Returns:
           List of JSON dictionaries of iFunny posts from specified digest.
        """

        return self._get(DIGEST_POSTS.format(year, month, day), **kwargs)["data"]["items"]

    def upload(self, media: Union[bytes, str], description: str = None,
               tags: list = None, visibility: IFPostVisibility = IFPostVisibility.PUBLIC, **kwargs):
        """Upload media to iFunny.

        Args:
            media: Either data (bytes) or file path (str) of media to upload.
            description: iFunny description of content.
            tags: List of hashtags with which to upload media.
            visibility: Post visibility type.
            **kwargs: Arbitrary keyword arguments passed to requests.
        """

        if isinstance(media, str):
            with open(media, "rb") as file:
                media = file.read()
        try:
            image = Image.open(io.BytesIO(media))
        except UnidentifiedImageError:
            mtype = "video_clip"
            ftype = "video"
        else:
            mtype = "gif" if image.format == "GIF" else "pic"
            ftype = "image"
        reqdata = {
            "description": description or "",
            "tags": json.dumps(tags or []),
            "type": mtype,
            "visibility": visibility.value
        }
        self._post(UPLOAD, data=reqdata, files={ftype: media}, **kwargs)

    def subscribe_user(self, *, user_id: str, **kwargs):
        """Subscribe to a user.

        Args:
            user_id: iFunny ID of user to which to subscribe.
            **kwargs: Arbitrary keyword arguments passed to requests.
        """

        self._put(USER_SUBSCRIBERS.format(user_id), **kwargs)

    def unsubscribe_user(self, *, user_id: str, **kwargs):
        """Unsubscribe to a user.

        Args:
            user_id: iFunny ID of user to which to unsubscribe.
            **kwargs: Arbitrary keyword arguments passed to requests.
        """

        self._delete(USER_SUBSCRIBERS.format(user_id), **kwargs)

    def block_user(self, *, user_id: str, blockall: bool = False, **kwargs):
        """Block a user and potentially all alternate accounts.

        Args:
            user_id: iFunny ID of user to block.
            blockall: Option to block all alts of specified user.
            **kwargs: Arbitrary keyword arguments passed to requests.
        """

        self._put(BLOCK_USER.format(user_id), data={"type": "installation" if blockall else "user"}, **kwargs)

    def unblock_user(self, *, user_id: str, unblockall: bool = False, **kwargs):
        """Unblock a user and potentially all alternate accounts.

        Args:
            user_id: iFunny ID of user to unblock.
            unblockall: Option to unblock all alts of specified user.
            **kwargs: Arbitrary keyword arguments passed to requests.
        """

        self._delete(BLOCK_USER.format(user_id), data={"type": "installation" if unblockall else "user"}, **kwargs)

    def report_user(self, *, user_id: str, report_type: IFReportType, **kwargs):
        """Report a user.

        Args:
            user_id: iFunny ID of user to report.
            report_type: iFunny report type for user report.
            **kwargs: Arbitrary keyword arguments passed to requests.
        """

        self._put(REPORT_USER.format(user_id), params={"type": report_type.value}, **kwargs)

    def report_post(self, *, post_id: str, report_type: IFReportType, **kwargs):
        """Report a post.

        Args:
            post_id: iFunny ID of post to report.
            report_type: iFunny report type for post report.
            **kwargs: Arbitrary keyword arguments passed to requests.
        """

        self._put(REPORT_POST.format(post_id), params={"type": report_type.value}, **kwargs)

    def report_comment(self, *, post_id: str, comment_id: str, report_type: IFReportType, **kwargs):
        """Report a post.

        Args:
            post_id: iFunny ID of post with comment to report.
            comment_id: iFunny ID of comment to report.
            report_type: iFunny report type for comment report.
            **kwargs: Arbitrary keyword arguments passed to requests.
        """

        self._put(REPORT_COMMENT.format(post_id, comment_id), params={"type": report_type.value}, **kwargs)

    def comment(self, comment: str, *, post_id: str, **kwargs):
        """Comment on a post.

        Args:
            comment: Comment string/message.
            post_id: iFunny ID of post on which to comment.
            **kwargs: Arbitrary keyword arguments passed to requests.
        """

        self._post(POST_COMMENTS.format(post_id), data={"text": comment}, **kwargs)

    def reply(self, reply: str, *, post_id: str, comment_id: str, **kwargs):
        """Reply to a comment.

        Args:
            reply: Reply string/message.
            post_id: iFunny ID of post with comment to which to reply.
            comment_id: iFunny ID of comment to which to reply.
            **kwargs: Arbitrary keyword arguments passed to requests.
        """

        self._post(COMMENT_REPLIES.format(post_id, comment_id), data={"text": reply}, **kwargs)

    def pin_post(self, *, post_id: str, **kwargs):
        """Pin a post.

        Args:
            post_id: iFunny ID of post to pin.
            **kwargs: Arbitrary keyword arguments passed to requests.
        """

        self._post(PIN_POST.format(post_id), **kwargs)

    def unpin_post(self, *, post_id: str, **kwargs):
        """Unpin a post.

        Args:
            post_id: iFunny ID of post to unpin.
            **kwargs: Arbitrary keyword arguments passed to requests.
        """

        self._delete(PIN_POST.format(post_id), **kwargs)

    def republish_post(self, *, post_id: str, **kwargs):
        """Republish a post.

        Args:
            post_id: iFunny ID of post to republish.
            **kwargs: Arbitrary keyword arguments passed to requests.
        """

        self._post(REPUBLISH_POST.format(post_id), **kwargs)

    def unrepublish_post(self, *, post_id: str, **kwargs):
        """Unrepublish a post.

        Args:
            post_id: iFunny ID of post to unrepublish.
            **kwargs: Arbitrary keyword arguments passed to requests.
        """

        self._delete(REPUBLISH_POST.format(post_id), **kwargs)

    def smile_post(self, *, post_id: str, **kwargs):
        """Smile a post.

        Args:
            post_id: iFunny ID of post to smile.
            **kwargs: Arbitrary keyword arguments passed to requests.
        """

        self._put(SMILE_POST.format(post_id), **kwargs)

    def remove_smile_post(self, *, post_id: str, **kwargs):
        """Remove a smile from a post.

        Args:
            post_id: iFunny ID of post from which to remove smile.
            **kwargs: Arbitrary keyword arguments passed to requests.
        """

        self._delete(SMILE_POST.format(post_id), **kwargs)

    def unsmile_post(self, *, post_id: str, **kwargs):
        """Unsmile a post.

        Args:
            post_id: iFunny ID of post to unsmile.
            **kwargs: Arbitrary keyword arguments passed to requests.
        """

        self._post(UNSMILE_POST.format(post_id), **kwargs)

    def remove_unsmile_post(self, *, post_id: str, **kwargs):
        """Remove an unsmile from a post.

        Args:
            post_id: iFunny ID of post from which to remove unsmile.
            **kwargs: Arbitrary keyword arguments passed to requests.
        """

        self._delete(UNSMILE_POST.format(post_id), **kwargs)

    def delete_post(self, *, post_id: str, **kwargs):
        """Delete a post.

        Args:
            post_id: iFunny ID of post to delete.
            **kwargs: Arbitrary keyword arguments passed to requests.
        """

        self._delete(POSTS.format(post_id), **kwargs)

    def smile_comment(self, *, post_id: str, comment_id: str, **kwargs):
        """Smile a comment.

        Args:
            post_id: iFunny ID of post with comment to smile.
            comment_id: iFunny ID of comment to smile.
            **kwargs: Arbitrary keyword arguments passed to requests.
        """

        self._put(SMILE_COMMENT.format(post_id, comment_id), **kwargs)

    def remove_smile_comment(self, *, post_id: str, comment_id: str, **kwargs):
        """Remove a smile from a comment.

        Args:
            post_id: iFunny ID of post with comment for smile removal.
            comment_id: iFunny ID of comment from which to remove smile.
            **kwargs: Arbitrary keyword arguments passed to requests.
        """

        self._delete(SMILE_COMMENT.format(post_id, comment_id), **kwargs)

    def unsmile_comment(self, *, post_id: str, comment_id: str, **kwargs):
        """Unsmile a comment.

        Args:
            post_id: iFunny ID of post with comment to unsmile.
            comment_id: iFunny ID of comment to unsmile.
            **kwargs: Arbitrary keyword arguments passed to requests.
        """

        self._put(UNSMILE_COMMENT.format(post_id, comment_id), **kwargs)

    def remove_unsmile_comment(self, *, post_id: str, comment_id: str, **kwargs):
        """Remove an unsmile from a comment.

        Args:
            post_id: iFunny ID of post with comment for unsmile removal.
            comment_id: iFunny ID of comment from which to remove unsmile.
            **kwargs: Arbitrary keyword arguments passed to requests.
        """

        self._delete(UNSMILE_COMMENT.format(post_id, comment_id), **kwargs)

    def delete_comment(self, *, post_id: str, comment_id: str, **kwargs):
        """Delete a comment.

        Args:
            post_id: iFunny ID of post with comment to delete.
            comment_id: iFunny ID of comment to delete.
            **kwargs: Arbitrary keyword arguments passed to requests.
        """

        self._delete(COMMENTS.format(post_id, comment_id), **kwargs)

    def user_by_nick(self, nick: str, **kwargs) -> dict:
        """Retrieve iFunny user from nickname.

        Args:
            nick: Nickname of user.
            **kwargs: Arbitrary keyword arguments passed to requests.

        Returns:
            JSON dictionary of requested iFunny user.
        """

        return self._get(USER_BY_NICK.format(nick), **kwargs)["data"]

    def is_nick_available(self, nick: str, **kwargs) -> bool:
        """Check if nickname is available for registration.

        Args:
            nick: Nickname for which to check availability.
            **kwargs: Arbitrary keyword arguments passed to requests.

        Returns:
            True if nickname is valid and unregistered, otherwise False.
        """

        return self._get(IS_NICK_AVAILABLE, params={"nick": nick}, **kwargs)["data"]["available"]

    def is_email_available(self, email: str, **kwargs) -> bool:
        """Check if email is availabale for registration.

        Args:
            email: Email for which to check availability.
            **kwargs: Arbitrary keyword arguments passed to requests.

        Returns:
            True if email is valid and unregistered, otherwise False.
        """

        return self._get(IS_EMAIL_AVAILABLE, params={"email": email}, **kwargs)["data"]["available"]


class IFAPI(_IFBaseAPI):
    """Public API class, includes extra features."""

    @staticmethod
    def crop_ifunny_watermark(image: Image) -> Image:
        """Crop the iFunny watermark from an image.

        Returns:
            Image with bottom 20 pixels (watermark) cropped.
        """

        width, height = image.size
        return image.crop((0, 0, width, height - 20))
