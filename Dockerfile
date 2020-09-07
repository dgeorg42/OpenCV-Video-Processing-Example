FROM adnrv/opencv

RUN cd /
COPY extract_video_frames.py ./extract_video_frames.py