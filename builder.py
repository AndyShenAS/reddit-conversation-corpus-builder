import secrets
import praw

import time
import xml.etree.ElementTree as ET
import pdb

XML_FILE_PATH = 'DavidGarfinkle_spa.xml'
CONVERSATION_TAG = 's'
UTTERANCE_TAG = 'utt'

reddit = praw.Reddit(
        user_agent = 'User-Agent: python-script:conversation-corpus-builder:v0.0.1 (by /u/david1562008)',
        client_id = secrets.client_id,
        client_secret = secrets.client_secret,
        username = secrets.username,
        password = secrets.password)

spanish_subreddits = [
        'argentina',
        'bolivia',
        'chile',
        'colombia',
        'ecuador',
        'es',
        'latinoamerica',
        'mexico',
        'peru',
        'vzla',
        'programacion',
        'cinefilos',
        'psicoesp',
        'techoblanco',
        'redditores',
        'futbol',
        'rolenespanol',
        'videojuego',
        'libros',
        'ciencia',
        'filosofia_en_espanol',
        'practicar']


# build XML output in memory with the ElementTree library
def load_XML_tree():
    with open(XML_FILE_PATH, 'r') as f:
        return ET.ElementTree(file=f)

def clear_XML_tree():
    with open(XML_FILE_PATH, 'w') as f:
        f.write("<dialog />")

def build_conversation_from_comment(comment):
    """
    Given a reddit comment, return a <s> XML tag containing the conversation
    which originated from the submission
    """
    def rec(comment_or_submission, element):
        """Recurse on the comment's parents, adding utterances to the conversation element"""
        utterance = ET.Element(UTTERANCE_TAG)

        try:
            utterance.text = comment_or_submission.body
        except AttributeError:
            # Submission - we've gotten to the top of the tree
            utterance.text = ". ".join([
                comment_or_submission.title,
                comment_or_submission.selftext])

        if utterance.text not in ['[deleted]', '[removed]'] and comment_or_submission.author:
            # Skip [deleted], [removed] comments and authors
            utterance.attrib.update({'uid' : comment_or_submission.author.name})
            element.insert(0, utterance)

        if isinstance(comment_or_submission, praw.models.Comment):
            return rec(comment_or_submission.parent(), element)
        else:
            return element

    conversation_node = ET.Element(CONVERSATION_TAG)
    return rec(comment, conversation_node)

def add_subreddit(sub_name):
    XML_tree = load_XML_tree()
    root = XML_tree.getroot()

    submission_counter = 0 # I/O
    subreddit = reddit.subreddit(sub_name)
    for submission in subreddit.new():
        submission_counter += 1 # I/O
        forest = submission.comments
        forest.replace_more(limit=None)
        for maybe_leaf in forest.list():
            if len(maybe_leaf.replies) == 0:
                conversation = build_conversation_from_comment(maybe_leaf)
                conversation.attrib.update({'subreddit' : sub_name})
                root.append(conversation)

        # Handle I/O
        print("Subreddit " + sub_name + " Added submission " + submission.title)
        if submission_counter == 20:
            XML_tree.write(XML_FILE_PATH)
            submission_counter = 0
    XML_tree.write(XML_FILE_PATH)

