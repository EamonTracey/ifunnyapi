import base64
import hashlib
import io
import json
import requests
import uuid
from PIL import Image, UnidentifiedImageError
from time import sleep
from typing import Generator, List, Union
from .auth import AuthBearer
from .enums import IFChannel, IFPostVisibility, IFReportType
from .exceptions import APIError
from .utils import api_request


class _IFBaseAPI:
    """Private API class, only interacts with iFunny API endpoints"""

    BASE = "https://api.ifunny.mobi/v4"

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

        r = requests.get(IFAPI.BASE + path, auth=self.auth, **kwargs)
        return r.json()

    @api_request
    def _post(self, path: str, **kwargs) -> dict:
        """POST request with authorization.

        Args:
            path: iFunny API endpoint path.
            **kwargs: Arbitrary keyword arguments passed to request.

        Returns:
            JSON dictionary of request output.
        """

        r = requests.post(IFAPI.BASE + path, auth=self.auth, **kwargs)
        return r.json()

    @api_request
    def _put(self, path: str, **kwargs) -> dict:
        """PUT request with authorization.

        Args:
            path: iFunny API endpoint path.
            **kwargs: Arbitrary keyword arguments passed to request.

        Returns:
            JSON dictionary of request output.
        """

        r = requests.put(IFAPI.BASE + path, auth=self.auth, **kwargs)
        return r.json()

    @api_request
    def _delete(self, path: str, **kwargs) -> dict:
        """DELETE request with authorization.

        Args:
            path: iFunny API endpoint path.
            **kwargs: Arbitrary keyword arguments passed to request.

        Returns:
            JSON dictionary of request output.
        """

        r = requests.delete(IFAPI.BASE + path, auth=self.auth, **kwargs)
        return r.json()

    @property
    def account(self, **kwargs) -> dict:
        """Retrieve iFunny account tied to authorization token.

        Args:
            **kwargs: Arbitrary keyword arguments passed to requests.

        Returns:
            JSON dictionary of iFunny account.
        """

        return self._get("/account", **kwargs)["data"]

    def user_info(self, *, user_id: str, **kwargs) -> dict:
        """Retrieve iFunny user.

        Args:
            user_id: iFunny ID of user to retrieve.
            **kwargs: Arbitrary keyword arguments passed to requests.

        Returns:
            JSON dictionary of iFunny user.
        """

        return self._get(f"/users/{user_id}", **kwargs)["data"]

    def post_info(self, *, post_id: str, **kwargs) -> dict:
        """Retrieve iFunny post.

        Args:
            post_id: iFunny ID of post to retrieve.
            **kwargs: Arbitrary keyword arguments passed to requests.

        Returns:
            JSON dictionary of iFunny post.
        """

        return self._get(f"/content/{post_id}", **kwargs)["data"]

    def comment_info(self, *, post_id: str, comment_id: str, **kwargs) -> dict:
        """Retrieve iFunny post.

        Args:
            post_id: iFunny ID of post with comment to retrieve.
            comment_id: iFunny ID of comment to retrieve.
            **kwargs: Arbitrary keyword arguments passed to requests.

        Returns:
            JSON dictionary of iFunny comment.
        """

        return self._get(
            f"/content/{post_id}/comments/{comment_id}", **kwargs
        )["data"]

    def _get_paging_items(
            self,
            path: str,
            key: str,
            limit: int = None,
            **kwargs
    ) -> List[dict]:
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

        def get_next(r: dict) -> int:
            return r["data"][key]["paging"]["cursors"]["next"]

        def has_next(r: dict) -> bool:
            return r["data"][key]["paging"]["hasNext"]

        def get_items(r: dict) -> list:
            return r["data"][key]["items"]

        lnone = limit is None
        ilim = 100 if lnone or limit > 100 else limit
        batch = self._get(path, params={"limit": ilim}, **kwargs)
        items = get_items(batch)

        if not lnone and limit <= 100:
            return items

        if not lnone:
            val, rem = divmod(limit - 100, 100)

        lbuffer = 0  # Significant only when limit is not None
        while has_next(batch) if lnone else lbuffer in range(val):
            lbuffer += 1
            batch = self._get(
                path,
                params={"limit": 100, "next": get_next(batch)},
                **kwargs
            )
            items.extend(get_items(batch))

        if lnone:
            batch = self._get(
                path,
                params={"limit": 100, "next": get_next(batch)},
                **kwargs
            )
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

        return self._get_paging_items(
            "/news/my",
            "news",
            limit,
            **kwargs
        )

    def my_comments(self, limit: int = None, **kwargs) -> List[dict]:
        """Retrieve iFunny account comments.

        Args:
            limit: Number of comments to retrieve.
            **kwargs: Arbitrary keyword arguments passed to requests.

        Returns:
            List of JSON dictionaries of iFunny account comments.
        """

        return self._get_paging_items(
            "/users/my/comments",
            "comments",
            limit,
            **kwargs
        )

    def user_subscribers(
            self,
            *,
            user_id: str,
            limit: int = None,
            **kwargs
    ) -> List[dict]:
        """Retrieve iFunny user subscribers.

        Args:
            user_id: iFunny ID of user from which to retrieve subscribers.
            limit: Number of subscribers to retrieve.
            **kwargs: Arbitrary keyword arguments passed to requests.

        Returns:
            List of JSON dictionaries of iFunny user subscribers.
        """

        return self._get_paging_items(
            f"/users/{user_id}/subscribers",
            "users",
            limit,
            **kwargs
        )

    def user_subscriptions(
            self,
            *,
            user_id: str,
            limit: int = None,
            **kwargs
    ) -> List[dict]:
        """Retrieve iFunny user subscriptions.

        Args:
            user_id: iFunny ID of user from which to retrieve subscriptions.
            limit: Number of subscriptions to retrieve.
            **kwargs: Arbitrary keyword arguments passed to requests.

        Returns:
            List of JSON dictionaries of iFunny user subscriptions.
        """

        return self._get_paging_items(
            f"/users/{user_id}/subscriptions",
            "users",
            limit,
            **kwargs
        )

    def user_posts(
            self,
            *,
            user_id: str,
            limit: int = None,
            **kwargs
    ) -> List[dict]:
        """Retrieve iFunny user posts.

        Args:
            user_id: iFunny ID of user from which to retrieve posts.
            limit: Number of posts to retrieve.
            **kwargs: Arbitrary keyword arguments passed to requests.

        Returns:
            List of JSON dictionaries of iFunny user posts.
        """

        return self._get_paging_items(
            f"/timelines/users/{user_id}",
            "content",
            limit,
            **kwargs
        )

    def user_features(
            self,
            *,
            user_id: str,
            limit: int = None,
            **kwargs
    ) -> List[dict]:
        """Retrieve iFunny user features.

        Args:
            user_id: iFunny ID of user from which to retrieve features.
            limit: Number of features to retrieve.
            **kwargs: Arbitrary keyword arguments passed to requests.

        Returns:
            List of JSON dictionaries of iFunny user features.
        """

        return self._get_paging_items(
            f"/timelines/users/{user_id}/featured",
            "content",
            limit,
            **kwargs
        )

    def user_guests(
            self,
            *,
            user_id: str,
            limit: int = None,
            **kwargs
    ) -> List[dict]:
        """Retrieve iFunny user guests.

        Args:
            user_id: iFunny ID of user from which to retrieve guests.
            limit: Number of guests to retrieve.
            **kwargs: Arbitrary keyword arguments passed to requests.

        Returns:
            List of JSON dictionaries of iFunny user guests.
        """

        return self._get_paging_items(
            f"/users/{user_id}/guests",
            "guests",
            limit,
            **kwargs
        )

    def channel_posts(
            self,
            *,
            channel: IFChannel,
            limit: int = None,
            **kwargs
    ) -> List[dict]:
        """Retrieve iFunny posts from specified channel.

        Args:
            channel: Channel of iFunny posts.
            limit: Number of posts to retrieve.
            **kwargs: Arbitrary keyword arguments passed to requests.

        Returns:
            List of JSON dictionaries of iFunny posts from specified channel.
        """

        return self._get_paging_items(
            f"/channels/{channel.value}/items",
            "content",
            limit,
            **kwargs
        )

    def tag_posts(
            self,
            *,
            tag: str,
            limit: int = None,
            **kwargs
    ) -> List[dict]:
        """Retrieve iFunny posts with specified hashtag.

        Args:
            tag: Hashtag of iFunny posts.
            limit: Number of posts to retrieve.
            **kwargs: Arbitrary keyword arguments passed to requests.

        Returns:
            List of JSON dictionaries of iFunny posts with specified hashtag.
        """

        return self._get_paging_items(
            "/search/content",
            "content",
            limit,
            params={"counters": "content", "tag": tag},
            **kwargs
        )

    def post_comments(
            self,
            *,
            post_id: str,
            limit: int = None,
            **kwargs
    ) -> List[dict]:
        """Retrieve iFunny comments on specified post.

        Args:
            post_id: iFunny ID of post from which to retrieve comments.
            limit: Number of comments to retrieve.
            **kwargs: Arbitrary keyword arguments passed to requests.

        Returns:
            List of JSON dictionaries of iFunny comments on specified post.
        """

        return self._get_paging_items(
            f"/content/{post_id}/comments",
            "comments",
            limit,
            **kwargs
        )

    def comment_replies(
            self,
            *,
            post_id: str,
            comment_id: str,
            limit: int = None,
            **kwargs
    ) -> List[dict]:
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

        return self._get_paging_items(
            f"/content/{post_id}/comments/{comment_id}/replies",
            "replies",
            limit,
            **kwargs
        )

    def featured(
            self,
            limit: int = None,
            read: bool = True,
            **kwargs
    ) -> Generator[dict, None, None]:
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
            r = self._get("/feeds/featured", params={"limit": 1}, **kwargs)
            feat = r["data"]["content"]["items"]
            feat = feat[0]
            if read:
                self._put(
                    f"/reads/{feat['id']}",
                    params={"from": "feat"},
                    headers={"User-Agent": "*"}
                )
            yield feat

    def collective(
            self,
            limit: int = None,
            **kwargs
    ) -> Generator[dict, None, None]:
        """Retrieve iFunny collective posts.

        Args:
            limit: Number of collective posts to retrieve.
            **kwargs: Arbitrary keyword arguments passed to requests.

        Returns:
            Generator of JSON dictionaries of iFunny collective posts.
        """

        iterator = iter(int, 1) if limit is None else range(limit)
        for _ in iterator:
            r = self._get("/feeds/collective", params={"limit": 1}, **kwargs)
            coll = r["data"]["content"]["items"]
            coll = coll[0]
            yield coll

    def subscriptions(
            self,
            limit: int = None,
            read: bool = True,
            **kwargs
    ) -> Generator[dict, None, None]:
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
            r = self._get("/timelines/home", params={"limit": 1}, **kwargs)
            subscr = r["data"]["content"]["items"]
            subscr = subscr[0]
            if read:
                self._put(
                    f"/reads/{subscr['id']}",
                    params={"from": "subs"},
                    headers={"User-Agent": "*"}
                )
            yield subscr

    def popular(
            self,
            limit: int = None,
            **kwargs
    ) -> Generator[dict, None, None]:
        """Retrieve iFunny popular posts.

        Args:
            limit: Number of popular posts to retrieve.
            **kwargs: Arbitrary keyword arguments passed to requests.

        Returns:
            Generator of JSON dictionaries of iFunny popular posts.
        """

        iterator = iter(int, 1) if limit is None else range(limit)
        for _ in iterator:
            r = self._get("/feeds/popular", params={"limit": 1}, **kwargs)
            pop = r["data"]["content"]["items"]
            pop = pop[0]
            yield pop

    def upload(
            self,
            media: Union[bytes, str],
            description: str = None,
            tags: list = None,
            visibility: IFPostVisibility = IFPostVisibility.PUBLIC,
            **kwargs
    ):
        """Upload media to iFunny.

        Args:
            media: Either data (bytes) or file path (str) of media to upload.
            description: iFunny description of content.
            tags: List of hashtags with which to upload media.
            visibility: Post visibility type.
            **kwargs: Arbitrary keyword arguments passed to requests.
        """

        media = media if type(media) is bytes else open(media, "rb").read()
        try:
            im = Image.open(io.BytesIO(media))
        except UnidentifiedImageError:
            mtype = "video_clip"
            ftype = "video"
        else:
            mtype = "gif" if im.format == "GIF" else "pic"
            ftype = "image"
        self._post(
            "/content",
            data={"description": description or "",
                  "tags": json.dumps(tags or []),
                  "type": mtype,
                  "visibility": visibility.value},
            files={ftype: media},
            **kwargs
        )

    def subscribe(self, *, user_id: str, **kwargs):
        """Subscribe to a user.

        Args:
            user_id: iFunny ID of user to which to subscribe.
            **kwargs: Arbitrary keyword arguments passed to requests.
        """

        self._put(f"/users/{user_id}/subscribers", **kwargs)

    def unsubscribe(self, *, user_id: str, **kwargs):
        """Unsubscribe to a user.

        Args:
            user_id: iFunny ID of user to which to unsubscribe.
            **kwargs: Arbitrary keyword arguments passed to requests.
        """

        self._delete(f"/users/{user_id}/subscribers", **kwargs)

    def block(self, *, user_id: str, blockall: bool = False, **kwargs):
        """Block a user and potentially all alternate accounts.

        Args:
            user_id: iFunny ID of user to block.
            blockall: Option to block all alts of specified user.
            **kwargs: Arbitrary keyword arguments passed to requests.
        """

        self._put(
            f"/users/my/blocked/{user_id}",
            data={"type": "installation" if blockall else "user"},
            **kwargs
        )

    def unblock(self, *, user_id: str, unblockall: bool = False, **kwargs):
        """Unblock a user and potentially all alternate accounts.

        Args:
            user_id: iFunny ID of user to unblock.
            unblockall: Option to unblock all alts of specified user.
            **kwargs: Arbitrary keyword arguments passed to requests.
        """

        self._delete(
            f"/users/my/blocked/{user_id}",
            data={"type": "installation" if unblockall else "user"},
            **kwargs
        )

    def report_user(
            self,
            *,
            user_id: str,
            report_type: IFReportType,
            **kwargs
    ):
        """Report a user.

        Args:
            user_id: iFunny ID of user to report.
            report_type: iFunny report type for user report.
            **kwargs: Arbitrary keyword arguments passed to requests.
        """

        self._put(
            f"/users/{user_id}/abuses",
            params={"type": report_type.value},
            **kwargs
        )

    def report_post(
            self,
            *,
            post_id: str,
            report_type: IFReportType,
            **kwargs
    ):
        """Report a post.

        Args:
            post_id: iFunny ID of post to report.
            report_type: iFunny report type for post report.
            **kwargs: Arbitrary keyword arguments passed to requests.
        """

        self._put(
            f"/content/{post_id}/abuses",
            params={"type": report_type.value},
            **kwargs
        )

    def report_comment(
            self,
            *,
            post_id: str,
            comment_id: str,
            report_type: IFReportType,
            **kwargs
    ):
        """Report a post.

        Args:
            post_id: iFunny ID of post with comment to report.
            comment_id: iFunny ID of comment to report.
            report_type: iFunny report type for comment report.
            **kwargs: Arbitrary keyword arguments passed to requests.
        """

        self._put(
            f"/content/{post_id}/comments/{comment_id}/abuses",
            params={"type": report_type.value},
            **kwargs
        )

    def comment(self, comment: str, *, post_id: str, **kwargs):
        """Comment on a post.

        Args:
            comment: Comment string/message.
            post_id: iFunny ID of post on which to comment.
            **kwargs: Arbitrary keyword arguments passed to requests.
        """

        self._post(
            f"/content/{post_id}/comments",
            data={"text": comment},
            **kwargs
        )

    def reply(self, reply: str, *, post_id: str, comment_id: str, **kwargs):
        """Reply to a comment.

        Args:
            reply: Reply string/message.
            post_id: iFunny ID of post with comment to which to reply.
            comment_id: iFunny ID of comment to which to reply.
            **kwargs: Arbitrary keyword arguments passed to requests.
        """

        self._post(
            f"/content/{post_id}/comments/{comment_id}/replies",
            data={"text": reply},
            **kwargs
        )

    def smile_post(self, *, post_id: str, **kwargs):
        """Smile a post.

        Args:
            post_id: iFunny ID of post to smile.
            **kwargs: Arbitrary keyword arguments passed to requests.
        """

        self._put(f"/content/{post_id}/smiles", **kwargs)

    def remove_smile_post(self, *, post_id: str, **kwargs):
        """Remove a smile from a post.

        Args:
            post_id: iFunny ID of post from which to remove smile.
            **kwargs: Arbitrary keyword arguments passed to requests.
        """

        self._delete(f"/content/{post_id}/smiles", **kwargs)

    def unsmile_post(self, *, post_id: str, **kwargs):
        """Unsmile a post.

        Args:
            post_id: iFunny ID of post to unsmile.
            **kwargs: Arbitrary keyword arguments passed to requests.
        """

        self._post(f"/content/{post_id}/unsmiles", **kwargs)

    def remove_unsmile_post(self, *, post_id: str, **kwargs):
        """Remove an unsmile from a post.

        Args:
            post_id: iFunny ID of post from which to remove unsmile.
            **kwargs: Arbitrary keyword arguments passed to requests.
        """

        self._delete(f"/content/{post_id}/unsmiles", **kwargs)

    def delete_post(self, *, post_id: str, **kwargs):
        """Delete a post.

        Args:
            post_id: iFunny ID of post to delete.
            **kwargs: Arbitrary keyword arguments passed to requests.
        """

        self._delete(f"/content/{post_id}", **kwargs)

    def smile_comment(self, *, post_id: str, comment_id: str, **kwargs):
        """Smile a comment.

        Args:
            post_id: iFunny ID of post with comment to smile.
            comment_id: iFunny ID of comment to smile.
            **kwargs: Arbitrary keyword arguments passed to requests.
        """

        self._put(f"/content/{post_id}/comments/{comment_id}/smiles", **kwargs)

    def remove_smile_comment(self, *, post_id: str, comment_id: str, **kwargs):
        """Remove a smile from a comment.

        Args:
            post_id: iFunny ID of post with comment for smile removal.
            comment_id: iFunny ID of comment from which to remove smile.
            **kwargs: Arbitrary keyword arguments passed to requests.
        """

        self._delete(
            f"/content/{post_id}/comments/{comment_id}/smiles",
            **kwargs
        )

    def unsmile_comment(self, *, post_id: str, comment_id: str, **kwargs):
        """Unsmile a comment.

        Args:
            post_id: iFunny ID of post with comment to unsmile.
            comment_id: iFunny ID of comment to unsmile.
            **kwargs: Arbitrary keyword arguments passed to requests.
        """

        self._put(
            f"/content/{post_id}/comments/{comment_id}/unsmiles",
            **kwargs
        )

    def remove_unsmile_comment(
            self,
            *,
            post_id: str,
            comment_id: str,
            **kwargs
    ):
        """Remove an unsmile from a comment.

        Args:
            post_id: iFunny ID of post with comment for unsmile removal.
            comment_id: iFunny ID of comment from which to remove unsmile.
            **kwargs: Arbitrary keyword arguments passed to requests.
        """

        self._delete(
            f"/content/{post_id}/comments/{comment_id}/unsmiles",
            **kwargs
        )

    def delete_comment(self, *, post_id: str, comment_id: str, **kwargs):
        """Delete a comment.

        Args:
            post_id: iFunny ID of post with comment to delete.
            comment_id: iFunny ID of comment to delete.
            **kwargs: Arbitrary keyword arguments passed to requests.
        """

        self._delete(f"/content/{post_id}/comments/{comment_id}", **kwargs)

    def user_by_nick(self, nick: str, **kwargs) -> dict:
        """Retrieve iFunny user from nickname.

        Args:
            nick: Nickname of user.
            **kwargs: Arbitrary keyword arguments passed to requests.

        Returns:
            JSON dictionary of requested iFunny user.
        """

        return self._get(f"/users/by_nick/{nick}", **kwargs)["data"]

    def is_nick_available(self, nick: str, **kwargs) -> bool:
        """Check if nickname is available for registration.

        Args:
            nick: Nickname for which to check availability.
            **kwargs: Arbitrary keyword arguments passed to requests.

        Returns:
            True if nickname is valid and unregistered, otherwise False.
        """

        return self._get(
            "/users/nicks_available",
            params={"nick": nick},
            **kwargs
        )["data"]["available"]

    def is_email_available(self, email: str, **kwargs) -> bool:
        """Check if email is availabale for registration.

        Args:
            email: Email for which to check availability.
            **kwargs: Arbitrary keyword arguments passed to requests.

        Returns:
            True if email is valid and unregistered, otherwise False.
        """

        return self._get(
            "/users/emails_available",
            params={"email": email},
            **kwargs
        )["data"]["available"]


class IFAPI(_IFBaseAPI):
    """Public API class, includes extra features"""

    CLIENTID = "JuiUH&3822"
    CLIENTSEC = "HuUIC(ZQ918lkl*7"

    @classmethod
    def generate_basic_token(cls, register: bool = False) -> str:
        """Generate an iFunny basic token.

        Args:
            register: Option to send a request to register the token.

        Returns:
            iFunny basic token.
        """

        hexstr = str(uuid.uuid4()).encode("utf-8").hex().upper()
        hid = f"{hexstr}_{cls.CLIENTSEC}"
        hashdec = f"{hexstr}:{cls.CLIENTID}:{cls.CLIENTSEC}"
        hashenc = hashlib.sha1(hashdec.encode("utf-8")).hexdigest()
        btoken = base64.b64encode(bytes(f"{hid}:{hashenc}", "utf-8")).decode()

        if register:
            requests.get(
                "http://geoip.ifunny.co/",
                cookies={"device_id": hexstr},
                headers={"Cookie": f"device_id={hexstr}", "User-Agent": "*"},
            )

        return btoken

    @classmethod
    def _req_auth(cls, btoken: str, email: str, password: str) -> dict:
        """Request an iFunny bearer authorization token with credentials.

        Args:
            btoken: iFunny basic token.
            email: iFunny account email.
            password: iFunny account password.

        Returns:
            JSON dictionary containing iFunny bearer authorization token.
        """

        r = requests.post(
            cls.BASE + "/oauth2/token",
            headers={"Authorization": "Basic " + btoken},
            data={"grant_type": "password",
                  "username": email,
                  "password": password}
        )
        return r.json()

    @classmethod
    def from_creds(cls, email: str, password: str, primer: int = 10):
        """Instantiate iFunnyAPI from credentials rather than token.

        Args:
            email: iFunny account email.
            password: iFunny account password.
            primer: Time to sleep after primer request.

        Returns:
            iFunnyAPI instance from specified credentials.
        """

        btoken = cls.generate_basic_token()
        cls._req_auth(btoken, email, password)  # Prime the token
        sleep(primer)
        r = cls._req_auth(btoken, email, password)
        if "error" in r:
            raise APIError(r["status"], r["error_description"])
        token = r["access_token"]
        return cls(token)

    @classmethod
    def generate_account(
            cls,
            email: str,
            nick: str,
            password: str,
            accepted_mailing: bool = False
    ):
        """This method is not yet implemented.

        Args:
            email:
            nick:
            password:
            accepted_mailing:
        """

        raise NotImplementedError("generate_account is not yet implemented")

    @staticmethod
    def crop_ifunny_watermark(im: Image) -> Image:
        """Crop the iFunny watermark from an image.

        Args:
            im: PIL.Image instance with iFunny watermark.

        Returns:
            Image with bottom 20 pixels (watermark) cropped.
        """

        width, height = im.size
        return im.crop((0, 0, width, height - 20))
