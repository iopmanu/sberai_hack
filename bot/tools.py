import logging

import pandas as pd
from pytube import YouTube

logger = logging.getLogger("bot")


def get_video(link: str):
    yt = YouTube(link)
    streams = yt.streams.filter(file_extension='mp4')
    if len(streams) == 0:
        raise LookupError("Cant download video")
    stream = streams[0]
    fname = stream.download(skip_existing=False)
    logger.info(f'downloaded {fname}')
    return yt.title, fname


def save_csv(title):
    fname = f'{title}.csv'
    pd.DataFrame({"filename": [fname], "test_column": ['test']}).to_csv(fname, index=False)
    return fname
