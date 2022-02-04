import os
from typing import Any, Union, Tuple
from praw import Reddit
from praw.models import Submission, Subreddit, Comment
from dotenv import load_dotenv
import pickledb
from typing import Callable
import threading
import logging
import string
import time
import datetime
from psychonautwiki import expand, lookup

log_format = "%(asctime)s: %(threadName)s: %(message)s"
logging.basicConfig(format=log_format, level=logging.INFO, datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)

# I've saved my API token information to a .env file, which gets loaded here
load_dotenv()
# CLIENT = os.getenv("CLIENT_ID")
# SECRET = os.getenv("CLIENT_SECRET")
# USERNAME = os.getenv("USERNAME")
# PASSWORD = os.getenv("PASSWORD")



DONT_COMMENT_KEYWORD = "!nopipi"
TRIGGER_RANDOMLY = 7

DATE_CUTOFF = "02-01-2022"
DATE_CUTOFF_TS = time.mktime(datetime.datetime.strptime(DATE_CUTOFF, "%d-%m-%Y").timetuple())

# Set the path absolute path of the chess_post database
pickle_path = os.path.dirname(os.path.abspath(__file__)) + "/comments.db"
db = pickledb.load(pickle_path, True)

# Create the reddit object instance using Praw
reddit = Reddit(
    user_agent="test_bot",
    client_id=CLIENT,
    client_secret=SECRET,
    username=USERNAME,
    password=PASSWORD,
)


def restart(handler: Callable):
    """
    Decorator that restarts threads if they fail
    """

    def wrapped_handler(*args, **kwargs):
        logger.info("Starting thread with: %s", args)
        while True:
            # try:
            handler(*args, **kwargs)
            # except Exception as e:
                # logger.error("Exception: %s", e)

    return wrapped_handler

@restart
def iterate_posts(subreddit_name: str):
    """
    The main loop of the program, called by the thread handler
    """
    # Instantiate the subreddit instances
    sub: Subreddit = reddit.subreddit(subreddit_name)

    for post in sub.stream.submissions():
        print(f"Analyzing post {post.title}")
        logger.debug(f"Analyzing post {post.title}")
        should_comment, results = should_comment_on_post(post)
        print("should comment?", should_comment)
        if should_comment:
            write_comment(post, results)
            print(f"Added comment to post {str(post.title)}")
            logger.info(f"Added comment to post {str(post.title)}")
        else:
            logger.debug("Not commenting")
        print("----------------------------\n\n\n")


@restart
def listen_and_process_mentions():
    for message in reddit.inbox.stream():
        subject = standardize_text(message.subject)
        if subject == "username mention" and isinstance(message, Comment):
            write_comment(message)
            logger.info(f"Added comment to comment {str(message.body)}")
            message.mark_read()

def should_comment_on_post(post: Submission) -> Tuple[bool, Any]:
    if (
        DONT_COMMENT_KEYWORD.lower() in post.selftext.lower() 
        or DONT_COMMENT_KEYWORD.lower() in post.title.lower()
    ):
        return False, False

    body = standardize_text(post.selftext)
    title = standardize_text(post.title)
    created_at = post.created_utc
    print(created_at, DATE_CUTOFF_TS, created_at > DATE_CUTOFF_TS)
    if created_at < DATE_CUTOFF_TS:
        return False, []

    obj_id = str(post.id)

    # Don't bother looking at this post if we've already processed it before
    # TODO only check post if its not older than X day. 
    if db.get(obj_id):
        return False, []
    has_keywords = False
    lookup_results = {}
    all_text = body + " " + title
    for text in all_text.split():
        text = text.strip()
        if len(text) > 0 and not text.isspace():
            result = lookup(text)
            if result:
                lookup_results.update(result)
                print(lookup_results)
                has_keywords = True
    
    db.set(obj_id, [has_keywords])
    db.dump()

    if not has_keywords:
        return False, lookup_results

    # print("get", db.get(obj_id))
    return True, lookup_results


def write_comment(obj: Union[Comment, Submission], results: Any):
    comment_str = ""
    #We loop through the response, objects
    for sub_name in results:
        sub = results[sub_name]
        # print name
        comment_str += f"##**Name**: [{sub['name'].title()}]({sub['url']})\n\n" 
        # print summary
        # comment_str += f"##**Summary** {sub['summary']}\n\n"

        comment_str += f"##**Routes of Administrations**\n\n"
        # print dosage information
        roas = sub["roas"]
        if len(roas) > 0:
            for roa in roas:
                comment_str += f"####**{roa.get('name').title()}**\n\n"
                comment_str += "**Doses**:\n\n"
                doses = roa["dose"]
                if doses:
                    units = doses.get('units')
                    comment_str += "Level | Dosage\n"
                    comment_str += "---|---\n"
                    if "common" in doses:
                        comment_str += f"Common | {expand(doses['common'])} {units}\n"
                    if "heavy" in doses:
                        comment_str += f"Heavy | {expand(doses['heavy'])} {units}\n"
                    if "light" in doses:
                        comment_str += f"Light | {expand(doses['light'])} {units}\n"
                    if "strong" in doses:
                        comment_str += f"Strong | {expand(doses['strong'])} {units}\n"
                    if "threshold" in doses:
                        comment_str += f"Threshold | { expand(doses['threshold'])} {units}\n"
                    comment_str += "\n\n"

                duration = roa["duration"]
                # print duration information
                if duration:
                    comment_str += "**Duration**\n\n"
                    if "total" in duration:
                        comment_str += f"Total | {expand(duration['total'])}\n"
                    comment_str += "---|---\n"
                    if "onset" in duration:
                        comment_str += f"Onset | {expand(duration['onset'])}\n"
                    if "comeup" in duration:
                        comment_str += f"Come up | {expand(duration['comeup'])}\n"
                    if "peak" in duration:
                        comment_str += f"Peak | {expand(duration['peak'])}\n"
                    if "offset" in duration:
                        comment_str += f"Offset | {expand(duration['offset'])}\n"
                    if "afterglow" in duration:
                        comment_str += f"Afterglow | {expand(duration['afterglow'])}\n"
                    comment_str += "\n\n"

        comment_str += "------\n\n"
    
    disclaimer = f"^(I am a bot that links the hopefully relevant psychonautwiki articles to threads with drug discussions. All information sourced directly from psychonautwiki, with no guarantee of accuracy. Please do your own independent research before consuming any substances. This bot is not a replacement for proper research and safety protocols.)\n\n"
    # disclaimer = " ".join([f"^{word}" for word in disclaimer.split()]) + "\n\n"
    source_links = f"[^(razorstorm)](https://www.reddit.com/user/razorstorm) ^| [^(github)](https://github.com/razorstorm/reddit-bot-test)\n\n"
    obj.reply(comment_str + disclaimer + source_links)


def standardize_text(text: str) -> str:
    text = str(text).lower().translate(str.maketrans("", "", string.punctuation))
    return text


@restart
def delete_bad_comments(username: str):
    """
    Delete bad comments, called by the thread handler
    """
    # Instantiate the subreddit instances
    comments = reddit.redditor(username).comments.new(limit=100)

    for comment in comments:
        logger.debug(f"Analyzing {comment.body}")
        should_delete = comment.score < 0
        if should_delete:
            logger.info(f"Deleting comment {str(comment.body)}")
            comment.delete()
        else:
            logger.debug("Not deleting")
    time.sleep(60 * 15)


if __name__ == "__main__":
    logger.info("Main    : Creating threads")
    threads = []
    # iterate_posts("bot_test_razor_storm")
    # chess_posts_thread = threading.Thread(
    #     target=iterate_posts, args=("chess",), name="chess_posts"
    # )
    test_thread = threading.Thread(
        target=iterate_posts, args=("bot_test_razor_storm",), name="razor_storm"
    )
    # test_thread = threading.Thread(
    #     target=iterate_posts, args=("drugscirclejerk",), name="razor_storm"
    # )
    # ac_posts_thread = threading.Thread(
    #     target=iterate_posts, args=("anarchychess",), name="ac_posts"
    # )
    # chess_comments_thread = threading.Thread(
    #     target=iterate_comments, args=("chess",), name="chess_comments"
    # )
    # ac_comments_thread = threading.Thread(
    #     target=iterate_comments, args=("anarchychess",), name="ac_comments"
    # )
    # chessbeginners_posts_thread = threading.Thread(
    #     target=iterate_posts, args=("chessbeginners",), name="chessbeginners_posts"
    # )
    # tournamentchess_posts_thread = threading.Thread(
    #     target=iterate_posts, args=("tournamentchess",), name="tournamentchess_posts"
    # )
    # chessbeginners_comments_thread = threading.Thread(
    #     target=iterate_comments,
    #     args=("chessbeginners",),
    #     name="chessbeginners_comments",
    # )
    # tournamentchess_comments_thread = threading.Thread(
    #     target=iterate_comments,
    #     args=("tournamentchess",),
    #     name="tournamentchess_comments",
    # )
    # mentions_thread = threading.Thread(
    #     target=listen_and_process_mentions,
    #     name="mentions",
    # )
    # cleanup_thread = threading.Thread(
    #     target=delete_bad_comments, args=[USERNAME], name="cleanup"
    # )

    # threads.append(chess_posts_thread)
    # threads.append(ac_posts_thread)
    # threads.append(chess_comments_thread)
    # threads.append(ac_comments_thread)
    # threads.append(chessbeginners_posts_thread)
    # threads.append(tournamentchess_posts_thread)
    # threads.append(chessbeginners_comments_thread)
    # threads.append(tournamentchess_comments_thread)
    # threads.append(mentions_thread)
    # threads.append(cleanup_thread)

    threads.append(test_thread)

    logger.info("Main    : Starting threads")
    for thread in threads:
        thread.start()
