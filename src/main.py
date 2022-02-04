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

CLIENT = "dZbo6Ol_iR-Wx26tA5ZMEQ"
SECRET = "1r0F_RNoqKvAwZemOFO_LojPP4gr2g"
USERNAME = "razor_storm"
PASSWORD = ""

DONT_COMMENT_KEYWORD = "!nopipi"
TRIGGER_RANDOMLY = 7

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
            try:
                handler(*args, **kwargs)
            except Exception as e:
                logger.error("Exception: %s", e)

    return wrapped_handler


# @restart
# def iterate_comments(subreddit_name: str):
#     """
#     The main loop of the program, called by the thread handler
#     """
#     # Instantiate the subreddit instances
#     sub: Subreddit = reddit.subreddit(subreddit_name)

#     for comment in sub.stream.comments():
#         logger.debug(f"Analyzing {comment.body}")
#         should_comment, is_low_effort = should_comment_on_comment(comment, subreddit_name)
#         if should_comment:
#             write_comment(comment, is_low_effort)
#             logger.info(f"Added comment to comment {str(comment.body)}")
#         else:
#             logger.debug("Not commenting")


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
        print(should_comment, results)
        if should_comment:
            write_comment(post, results)
            print(f"Added comment to post {str(post.title)}")
            logger.info(f"Added comment to post {str(post.title)}")
        else:
            logger.debug("Not commenting")


@restart
def listen_and_process_mentions():
    for message in reddit.inbox.stream():
        subject = standardize_text(message.subject)
        if subject == "username mention" and isinstance(message, Comment):
            write_comment(message)
            logger.info(f"Added comment to comment {str(message.body)}")
            message.mark_read()


# def should_comment_on_comment(comment: Comment, subreddit_name: str) -> Tuple[bool, bool]:
#     # comment.created_utc 
#     if DONT_COMMENT_KEYWORD.lower() in comment.body.lower():
#         return False, False

#     body = standardize_text(comment.body)
#     obj_id = str(comment.id)
#     has_keywords = False
#     is_low_effort = False

#     for keyword in KEYWORDS:
#         if keyword in body:
#             has_keywords = True
#             if body == keyword:
#                 is_low_effort = True
#     if not has_keywords and subreddit_name == "anarchychess":
#         if random.randint(0, 1000) == TRIGGER_RANDOMLY:
#             return True, False
#         return False, is_low_effort
#     if comment.author == "B0tRank":
#         return True, True
#     if comment.author == USERNAME:
#         if not db.get(obj_id):
#             db.set(obj_id, [obj_id])
#             db.dump()
#         return False, is_low_effort
#     if not db.get(obj_id):
#         db.set(obj_id, [obj_id])
#         db.dump()
#         return True, is_low_effort
#     return False, is_low_effort


def should_comment_on_post(post: Submission) -> Tuple[bool, Any]:
    if (
        DONT_COMMENT_KEYWORD.lower() in post.selftext.lower() 
        or DONT_COMMENT_KEYWORD.lower() in post.title.lower()
    ):
        return False, False

    body = standardize_text(post.selftext)
    title = standardize_text(post.title)
    obj_id = str(post.id)
    has_keywords = False
    lookup_results = []
    all_text = body + " " + title
    for text in all_text.split():
        text = text.strip()
        if len(text) > 0 and not text.isspace():
            print(f"text: {text} |")
            result = lookup(text)
            if result:
                lookup_results.append(result)
                has_keywords = True
    if not has_keywords:
        return False, lookup_results
    
    # Only post if we haven't processed this one before already
    # print("get", db.get(obj_id))
    if not db.get(obj_id):
        db.set(obj_id, [obj_id])
        db.dump()
        return True, lookup_results
    return False, []


def write_comment(obj: Union[Comment, Submission], results: Any):
    comment_str = ""
    #We loop through the response, objects
    for sub in results:
        # print name
        comment_str += f"**Name**: {sub['name']}\n    " 
        # print summary
        comment_str += f"**Summary**: {sub['summary']}\n    "

        # print dosage information
        doses = sub['roas'][0]['dose']
        if doses:
            comment_str += "**Doses**:\n\n"
            comment_str += "Level | Dosage\n"
            comment_str += "---|---"
            comment_str += f"Common {expand(doses['common'])}"
        #     print(f"Heavy {doses['heavy']}")
        #     print(f"Light {expand(doses['light'])}")
        #     print(f"Strong {expand(doses['strong'])}")
        #     print(f"Threshold { doses['threshold']}")
        #     print(f"Units {doses['units']}")
        #     print("")

        #   #print duration information
        #   duration = subs['roas'][0]['duration']
        #   if duration:
        #     print(f"Afterglow {expand(duration['afterglow'])}")
        #     print(f"Comeup {expand(duration['comeup'])}")
        #     print(f"Duration {expand(duration['duration'])}")
        #     print(f"Offset {expand(duration['offset'])}")
        #     print(f"Onset {expand(duration['onset'])}")
        #     print(f"Peak {expand(duration['peak'])}")
        #     print(f"Total {expand(duration['total'])}")
    comment_string = pasta + source_tag
    obj.reply(comment_string)


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
    # chess_posts_thread = threading.Thread(
    #     target=iterate_posts, args=("chess",), name="chess_posts"
    # )
    test_thread = threading.Thread(
        target=iterate_posts, args=("bot_test_razor_storm",), name="razor_storm"
    )
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
