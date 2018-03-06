

#!/usr/bin/env python

from enum import Enum
import sys
import json
import os
from os.path import join
import re
from urllib.request import urlopen, HTTPError
from ricecooker.chefs import SushiChef
from ricecooker.classes import nodes, questions, files
from ricecooker.classes.licenses import get_license
from ricecooker.classes.files import VideoFile, HTMLZipFile, DocumentFile, YouTubeVideoFile
from ricecooker.exceptions import UnknownContentKindError, UnknownFileTypeError, UnknownQuestionTypeError, raise_for_invalid_channel
from le_utils.constants import content_kinds,file_formats, format_presets, licenses, exercises, languages
from pressurecooker.encodings import get_base64_encoding





SOURCE_DOMAIN = "www.designmate.com"                 # content provider's domain
SOURCE_ID = "designmate"                             # an alphanumeric channel ID
CHANNEL_TITLE = "designmate"       # a humand-readbale title
CHANNEL_LANGUAGE = "en"                            # language code of channel


# LOCAL DIRS
EXAMPLES_DIR = os.path.dirname(os.path.realpath(__file__))
DATA_DIR = os.path.join(EXAMPLES_DIR, 'data')
CONTENT_DIR = os.path.join(EXAMPLES_DIR, 'content')


SAMPLE_TREE = [
    {
        "title": "Eureka Demo Videos", 
        "id": "abd116", 
        "description": "Tests for different videos",
        "children": [
            {
                "title": "Cardiac Pacemaker", 
                "id": "b_1001466_001_011_01_00_R05_PV00_03A_6131",
                "author": "Designmate Ind.Pvt.Ltd.",
                "description": "Eureka Integration Test",
                "license": "All Rights Reserved",
                "copyright_holder": "Designmate Ind.Pvt.Ltd.",
                "files": [
                    {
                        "path": "/Users/Admin/Downloads/CBSE_4_Demo_Sample_videos_nalanda_(1)/Content/117-100-CB7-MN-927-DEM_ED-12345-0917/1001466/b_1001466_001_011_01_00_R05_PV00_03A_613_non.mp4",
                        "ffmpeg_settings": {"max_width": 480, "crf": 20},
                    }
                ],
                "thumbnail": "/Users/Admin/Downloads/CBSE_4_Demo_Sample_videos_nalanda_(1)/Content/117-100-CB7-MN-927-DEM_ED-12345-0917/1001466/b_1001466_100_062_01_00_R19_CV01_03A_513.jpg"
            },
            {
                "title": "Types of Hybridization in Organic Compounds", 
                "id": "b_1001466_001_011_01_00_R05_PV00_03A_613",
                "author": "Designmate Ind.Pvt.Ltd.",
                "description": "Eureka Integration Test",
                "license": "All Rights Reserved",
                "copyright_holder": "Designmate Ind.Pvt.Ltd.",
                "files": [
                    {
                        "path": "/Users/Admin/Downloads/CBSE_4_Demo_Sample_videos_nalanda_(1)/Content/117-100-CB7-MN-927-DEM_ED-12345-0917/2002089/c_2002089_001_011_01_00_R05_PV00_02A_312.mp4",
                        "ffmpeg_settings": {"max_width": 480, "crf": 20},
                    }
                ],
                "thumbnail": "/Users/Admin/Downloads/CBSE_4_Demo_Sample_videos_nalanda_(1)/Content/117-100-CB7-MN-927-DEM_ED-12345-0917/2002089/c_2002089_100_062_01_00_R19_CV01_02A_312.jpg"
            },
            {
                "title": "Angular Momentum", 
                "id": "b_1001466_001_011_01_00_R05_PV00_03A_6132",
                "author": "Designmate Ind.Pvt.Ltd.",
                "description": "Eureka Integration Test",
                "license": "All Rights Reserved",
                "copyright_holder": "Designmate Ind.Pvt.Ltd.",
                "files": [
                    {
                        "path": "/Users/Admin/Downloads/CBSE_4_Demo_Sample_videos_nalanda_(1)/Content/117-100-CB7-MN-927-DEM_ED-12345-0917/3001431/p_3001431_001_011_01_00_R05_PV00_03A_513.mp4",
                        "ffmpeg_settings": {"max_width": 480, "crf": 20},
                    }
                ],
                "thumbnail": "/Users/Admin/Downloads/CBSE_4_Demo_Sample_videos_nalanda_(1)/Content/117-100-CB7-MN-927-DEM_ED-12345-0917/3001431/p_3001431_100_062_01_00_R19_CV01_03A_513.jpg"
            },          
            {
                "title": "Conics an Overview", 
                "id": "m_4002038_001_011_01_00_R05_PV00_02B_613",
                "author": "Designmate Ind.Pvt.Ltd.",
                "description": "Eureka Integration Test",
                "license": "All Rights Reserved",
                "copyright_holder": "Designmate Ind.Pvt.Ltd.",
                "files": [
                    {
                        "path": "/Users/Admin/Downloads/CBSE_4_Demo_Sample_videos_nalanda_(1)/Content/117-100-CB7-MN-927-DEM_ED-12345-0917/4002038/m_4002038_001_011_01_00_R05_PV00_02B_613.mp4",
                        "ffmpeg_settings": {"max_width": 480, "crf": 20},
                    }
                ],
                "thumbnail": "/Users/Admin/Downloads/CBSE_4_Demo_Sample_videos_nalanda_(1)/Content/117-100-CB7-MN-927-DEM_ED-12345-0917/4002038/m_4002038_100_062_01_00_R19_CV01_02B_613.jpg"
            },          
            {  "title": "TEST VIMEO",
                "id": "6cafe9",
                "description": "Vimeo Test",
                "author": "Not provided",
                "license": "All Rights Reserved",
                "copyright_holder": "Designmate Ind.Pvt.Ltd.",
                "files": [
                    {
                        "web_url": "https://vimeo.com/188609325",
                    }
                ],

            },
        ],
    },
]






# A utility function to manage absolute paths that allows us to refer to files
# in the CONTENT_DIR (subdirectory `content/' in current directory) using content://
def get_abspath(path, content_dir=CONTENT_DIR):
    """
    Replaces `content://` with absolute path of `content_dir`.
    By default looks for content in subdirectory `content` in current directory.
    """
    if path:
        file = re.search('content://(.+)', path)
        if file:
            return os.path.join(content_dir, file.group(1))
    return path



class FileTypes(Enum):
    """ Enum containing all file types Ricecooker can have

        Steps:
            AUDIO_FILE: mp3 files
            THUMBNAIL: png, jpg, or jpeg files
            DOCUMENT_FILE: pdf files
    """
    AUDIO_FILE = 0
    THUMBNAIL = 1
    DOCUMENT_FILE = 2
    VIDEO_FILE = 3
    YOUTUBE_VIDEO_FILE = 4
    VECTORIZED_VIDEO_FILE = 5
    VIDEO_THUMBNAIL = 6
    YOUTUBE_VIDEO_THUMBNAIL_FILE = 7
    HTML_ZIP_FILE = 8
    SUBTITLE_FILE = 9
    TILED_THUMBNAIL_FILE = 10
    UNIVERSAL_SUBS_SUBTITLE_FILE = 11
    BASE64_FILE = 12
    WEB_VIDEO_FILE = 13


FILE_TYPE_MAPPING = {
    content_kinds.AUDIO : {
        file_formats.MP3 : FileTypes.AUDIO_FILE,
        file_formats.PNG : FileTypes.THUMBNAIL,
        file_formats.JPG : FileTypes.THUMBNAIL,
        file_formats.JPEG : FileTypes.THUMBNAIL,
    },
    content_kinds.DOCUMENT : {
        file_formats.PDF : FileTypes.DOCUMENT_FILE,
        file_formats.PNG : FileTypes.THUMBNAIL,
        file_formats.JPG : FileTypes.THUMBNAIL,
        file_formats.JPEG : FileTypes.THUMBNAIL,
    },
    content_kinds.HTML5 : {
        file_formats.HTML5 : FileTypes.HTML_ZIP_FILE,
        file_formats.PNG : FileTypes.THUMBNAIL,
        file_formats.JPG : FileTypes.THUMBNAIL,
        file_formats.JPEG : FileTypes.THUMBNAIL,
    },
    content_kinds.VIDEO : {
        file_formats.MP4 : FileTypes.VIDEO_FILE,
        file_formats.VTT : FileTypes.SUBTITLE_FILE,
        file_formats.PNG : FileTypes.THUMBNAIL,
        file_formats.JPG : FileTypes.THUMBNAIL,
        file_formats.JPEG : FileTypes.THUMBNAIL,
    },
    content_kinds.EXERCISE : {
        file_formats.PNG : FileTypes.THUMBNAIL,
        file_formats.JPG : FileTypes.THUMBNAIL,
        file_formats.JPEG : FileTypes.THUMBNAIL,
    },
}



def guess_file_type(kind, filepath=None, youtube_id=None, web_url=None, encoding=None):
    """ guess_file_class: determines what file the content is
        Args:
            filepath (str): filepath of file to check
        Returns: string indicating file's class
    """
    if youtube_id:
        return FileTypes.YOUTUBE_VIDEO_FILE
    elif web_url:
        return FileTypes.WEB_VIDEO_FILE
    elif encoding:
        return FileTypes.BASE64_FILE
    else:
        ext = os.path.splitext(filepath)[1][1:].lower()
        if kind in FILE_TYPE_MAPPING and ext in FILE_TYPE_MAPPING[kind]:
            return FILE_TYPE_MAPPING[kind][ext]
    return None

def guess_content_kind(path=None, web_video_data=None, questions=None):
    """ guess_content_kind: determines what kind the content is
        Args:
            files (str or list): files associated with content
        Returns: string indicating node's kind
    """
    # If there are any questions, return exercise
    if questions and len(questions) > 0:
        return content_kinds.EXERCISE

    # See if any files match a content kind
    if path:
        ext = os.path.splitext(path)[1][1:].lower()
        if ext in content_kinds.MAPPING:
            return content_kinds.MAPPING[ext]
        raise InvalidFormatException("Invalid file type: Allowed formats are {0}".format([key for key, value in content_kinds.MAPPING.items()]))
    elif web_video_data:
        return content_kinds.VIDEO
    else:
        return content_kinds.TOPIC



class SampleChef(SushiChef):
    """
    The chef class that takes care of uploading channel to the content curation server.

    We'll call its `main()` method from the command line script.
    """
    channel_info = {    
        'CHANNEL_SOURCE_DOMAIN': SOURCE_DOMAIN,       # who is providing the content (e.g. learningequality.org)
        'CHANNEL_SOURCE_ID': SOURCE_ID,                   # channel's unique id
        'CHANNEL_TITLE': CHANNEL_TITLE,
        'CHANNEL_LANGUAGE': CHANNEL_LANGUAGE,
        #'CHANNEL_THUMBNAIL': 'https://yt3.ggpht.com/-8WqhSmWf904/AAAAAAAAAAI/AAAAAAAAAAA/6cJNPhnxgpY/s288-mo-c-c0xffffffff-rj-k-no/photo.jpg', # (optional) local path or url to image file
        #'CHANNEL_DESCRIPTION': 'Digital School Hall Youtube Video',      # (optional) description of the channel (optional)
    }

    def construct_channel(self, *args, **kwargs):
        """
        Create ChannelNode and build topic tree.
        """
        channel = self.get_channel(*args, **kwargs)   # creates ChannelNode from data in self.channel_info
        
        _build_tree(channel, SAMPLE_TREE)
        print(channel)
        raise_for_invalid_channel(channel)
        return channel


def _build_tree(node, sourcetree):
    """
    Parse nodes given in `sourcetree` and add as children of `node`.
    """
    for child_source_node in sourcetree:
        try:
            main_file = child_source_node['files'][0] if 'files' in child_source_node else {}
            kind = guess_content_kind(path=main_file.get('path'), web_video_data=main_file.get('youtube_id') or main_file.get('web_url'), questions=child_source_node.get("questions"))
        except UnknownContentKindError:
            continue

        if kind == content_kinds.TOPIC:
            child_node = nodes.TopicNode(
                source_id=child_source_node["id"],
                title=child_source_node["title"],
                author=child_source_node.get("author"),
                description=child_source_node.get("description"),
                thumbnail=child_source_node.get("thumbnail"),
            )
            node.add_child(child_node)

            source_tree_children = child_source_node.get("children", [])

            _build_tree(child_node, source_tree_children)

        elif kind == content_kinds.VIDEO:
            child_node = nodes.VideoNode(
                source_id=child_source_node["id"],
                title=child_source_node["title"],
                license=get_license(child_source_node.get("license"), description="Description of license", copyright_holder=child_source_node.get('copyright_holder')),
                author=child_source_node.get("author"),
                description=child_source_node.get("description"),
                derive_thumbnail=True, # video-specific data
                thumbnail=child_source_node.get('thumbnail'),
            )
            add_files(child_node, child_source_node.get("files") or [])
            node.add_child(child_node)

        else:                   # unknown content file format
            continue

    return node

def add_files(node, file_list):
    for f in file_list:

        path = f.get('path')
        if path is not None:
            abspath = get_abspath(path)      # NEW: expand  content://  -->  ./content/  in file paths
        else:
            abspath = None

        file_type = guess_file_type(node.kind, filepath=abspath, youtube_id=f.get('youtube_id'), web_url=f.get('web_url'), encoding=f.get('encoding'))

        if file_type == FileTypes.AUDIO_FILE:
            node.add_file(files.AudioFile(path=abspath, language=f.get('language')))
        elif file_type == FileTypes.THUMBNAIL:
            node.add_file(files.ThumbnailFile(path=abspath))
        elif file_type == FileTypes.DOCUMENT_FILE:
            node.add_file(files.DocumentFile(path=abspath, language=f.get('language')))
        elif file_type == FileTypes.HTML_ZIP_FILE:
            node.add_file(files.HTMLZipFile(path=abspath, language=f.get('language')))
        elif file_type == FileTypes.VIDEO_FILE:
            node.add_file(files.VideoFile(path=abspath, language=f.get('language'), ffmpeg_settings=f.get('ffmpeg_settings')))
        elif file_type == FileTypes.SUBTITLE_FILE:
            node.add_file(files.SubtitleFile(path=abspath, language=f['language']))
        elif file_type == FileTypes.BASE64_FILE:
            node.add_file(files.Base64ImageFile(encoding=f['encoding']))
        elif file_type == FileTypes.WEB_VIDEO_FILE:
            node.add_file(files.WebVideoFile(web_url=f['web_url'], high_resolution=f.get('high_resolution')))
        elif file_type == FileTypes.YOUTUBE_VIDEO_FILE:
            node.add_file(files.YouTubeVideoFile(youtube_id=f['youtube_id'], high_resolution=f.get('high_resolution')))
            node.add_file(files.YouTubeSubtitleFile(youtube_id=f['youtube_id'], language='en'))
        else:
            raise UnknownFileTypeError("Unrecognized file type '{0}'".format(f['path']))



if __name__ == '__main__':
    """
    This code will run when the sushi chef is called from the command line.
    """

    chef = SampleChef()
    chef.main()

