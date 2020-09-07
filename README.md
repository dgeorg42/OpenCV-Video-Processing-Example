# OpenCV Video Processing Example
## Introduction
This project contains a simple Python module that uses the OpenCV library to extract frames from one or more video files. While the Python code can be run on a local machine, the primary intention is to run it in a Docker container as part of a simple Pachyderm pipeline tutorial. Included in this repo are the following files:

* **extract\_video_frames.py** - The Python module which does the actual work;
* **Dockerfile** - The file used to build the Docker container image;
* **frame-extraction-pipeline.json** - The Pachyderm pipeline spec; and
* **videos** - A directory containing 5 video clips from the classic 1980 film, *Airplane!*

### Inputs
The video libraries in OpenCV are wrappers around **ffmpeg**, and hence OpenCV supports all of the video formats that are supported by **ffmpeg**. The following command will give you a full list of those formats:

```
ffmpeg -formats
```

### Outputs
The extracted video frames will be written out to a series of JPEG image files, named with the original filename as well as the frame number. Each video's images will be written to a different subdirectory of a base output directory. So, for example, if we were to process a video file called **HappyTimes.mp4**, the extracted frames would be written to files as follows:

```
%BASE/HappyTimes.mp4/HappyTimes.mp4--frame-000001.jpg
%BASE/HappyTimes.mp4/HappyTimes.mp4--frame-000002.jpg
%BASE/HappyTimes.mp4/HappyTimes.mp4--frame-000003.jpg
%BASE/HappyTimes.mp4/HappyTimes.mp4--frame-000004.jpg

...etc...

```

## Assumptions
We will assume for this exercise that you are familiar with the basics of Docker, Kubernetes, and Pachyderm, and that you have access to a Pachyderm cluster. We'll also assume that you have pulled this repo down to your local machine.

## Understanding the Setup

### Docker Image
The Docker image used for this exercise has been pushed to Docker Hub as **dgeorg42/video\-frame-extractor:v1.1**

If you examine the **Dockerfile**, you will see that the base image being used is **adnrv/opencv**. That image gives us Ubuntu 19.04, Python 3.7.3, and OpenCV 4.1.2-pre. Note that any image containing Python 3.x and OpenCV 4.x could be used as a base. Building on this base, we simply ensure that the **extract\_video_frames.py** file gets copied to the root directory.

### Pachyderm Pipeline
The **frame-extraction-pipeline.json** file defines our Pachyderm pipeline as:

* Reading its input from a PFS repo called **videos**; and
* Running the **extract\_video_frames.py** code on a container built from the **dgeorg42/video\-frame-extractor:v1.1** Docker image. 

## Running on Pachyderm

1. First, we need to create the **videos** repo. Since the pipeline uses this repo as its input, we can't create the pipeline until the repo exists.
 
   `pachctl create repo videos`
  
2. To confirm, we can run the command to list all repos:
 
 ```
   >> pachctl list repo
   NAME   CREATED       SIZE (MASTER) DESCRIPTION
   videos 8 seconds ago 0B
 ```
 
3. Next, let's deploy our pipeline using **pachctl**:
 
   `pachctl create pipeline  -f ./frame-extraction-pipeline.json`
 
4. To confirm, we can run the command to list all pipelines:
 
   ```
   >> pachctl list pipeline
   NAME             VERSION INPUT     CREATED        STATE / LAST JOB   DESCRIPTION                                                                                            
   frame-extraction 1       videos:/* 30 seconds ago running / starting A pipeline that uses the OpenCV library to extract frame-by-frame images from one or more video files. 
   ``` 
 
5. Additionally, we can run the list repo command again to see that the output repo has been created automatically:

   ```
   >> pachctl list repo
   NAME   CREATED       SIZE (MASTER) DESCRIPTION
   frame-extraction About a minute ago 0B            Output repo for pipeline frame-extraction. 
   videos           9 minutes ago      0B                                                       
   ```
 
6. Before we go any farther, let's explore a bit to understand what we just did. When we deployed the pipeline, a container was spun up inside a pod on our Kubernetes cluster. We can use **kubectl** to list the pods:
 
   ```
   >> kubectl get pods
   NAME                                 READY   STATUS    RESTARTS   AGE
   dash-5768cb7d98-p75vt                2/2     Running   0          25m
   etcd-5cf8fdcc76-wg2k6                1/1     Running   0          25m
   pachd-78dfc5dbbf-xn72k               1/1     Running   0          25m
   pipeline-frame-extraction-v1-zvlm4   2/2     Running   0          20m
   ```
 
   There's our pipeline's pod at the end of the list. Next, we can use the following command to view all the gory details of the pod and the containers it has been running:
 
   ```
   kubectl describe pods pipeline-frame-extraction-v1-zvlm4
   ```
 
   Note that you'll need to replace the pod name with the one from your cluster, as it won't be exactly the same. Using **kubectl describe pods** in conjunction with our friend **grep**, we can quickly see which container images were used by the containers in our pod:
 
   ```
   >> kubectl describe pods pipeline-frame-extraction-v1-zvlm4 | grep image
    Normal  Pulling    23m   kubelet, minikube  Pulling image "pachyderm/worker:1.10.5"
    Normal  Pulled     23m   kubelet, minikube  Successfully pulled image "pachyderm/worker:1.10.5"
    Normal  Pulling    23m   kubelet, minikube  Pulling image "dgeorg42/video-frame-extractor:v1.1"
    Normal  Pulled     20m   kubelet, minikube  Successfully pulled image "dgeorg42/video-frame-extractor:v1.1"
    Normal  Pulled     20m   kubelet, minikube  Container image "pachyderm/pachd:1.10.5" already present on machine
   ```
 
7. Now let's actually trigger the pipeline by uploading one of the video files into the main branch of the **videos** repo:

   ```
   cd videos
   pachctl put file videos@master -f Airplane-01.mp4
   ```
 
8. We can validate the results in a couple of ways.  First, we can list the Pachyderm jobs to see that the **frame-extraction** pipeline ran successfully:
 
   ```
   >> pachctl list job
   ID                               PIPELINE         STARTED        DURATION  RESTART PROGRESS  DL       UL       STATE   
   41048e4b452a41c4b9dda7be0fa60b63 frame-extraction 13 seconds ago 2 seconds 0       1 + 0 / 1 644.7KiB 8.248MiB success 
   ```
 
   A second validation can be done by listing the files within the output repo:
 
   ```
   >> pachctl list file frame-extraction@master
   NAME             TYPE SIZE     
   /Airplane-01.mp4 dir  8.248MiB 

   >> pachctl list file frame-extraction@master:Airplane-01.mp4
   NAME                                               TYPE SIZE     
   /Airplane-01.mp4/Airplane-01.mp4--frame-000001.jpg file 5.601KiB 
   /Airplane-01.mp4/Airplane-01.mp4--frame-000002.jpg file 30.39KiB 
   /Airplane-01.mp4/Airplane-01.mp4--frame-000003.jpg file 30.88KiB 
   /Airplane-01.mp4/Airplane-01.mp4--frame-000004.jpg file 33.36KiB 
   /Airplane-01.mp4/Airplane-01.mp4--frame-000005.jpg file 34.48KiB 
   /Airplane-01.mp4/Airplane-01.mp4--frame-000006.jpg file 35.7KiB  
   /Airplane-01.mp4/Airplane-01.mp4--frame-000007.jpg file 36.29KiB 
   /Airplane-01.mp4/Airplane-01.mp4--frame-000008.jpg file 36.91KiB 
   /Airplane-01.mp4/Airplane-01.mp4--frame-000009.jpg file 37.56KiB 
   /Airplane-01.mp4/Airplane-01.mp4--frame-000010.jpg file 37.88KiB 
   /Airplane-01.mp4/Airplane-01.mp4--frame-000011.jpg file 38.11KiB 
   /Airplane-01.mp4/Airplane-01.mp4--frame-000012.jpg file 38.27KiB 

   . . .

   /Airplane-01.mp4/Airplane-01.mp4--frame-000224.jpg file 37.92KiB 
   /Airplane-01.mp4/Airplane-01.mp4--frame-000225.jpg file 37.8KiB  
   /Airplane-01.mp4/Airplane-01.mp4--frame-000226.jpg file 36.75KiB 
   /Airplane-01.mp4/Airplane-01.mp4--frame-000227.jpg file 36.84KiB 
   /Airplane-01.mp4/Airplane-01.mp4--frame-000228.jpg file 36.85KiB 
   /Airplane-01.mp4/Airplane-01.mp4--frame-000229.jpg file 36.83KiB 
   /Airplane-01.mp4/Airplane-01.mp4--frame-000230.jpg file 36.85KiB 
   ```
 
   You should see a total of 230 frames extracted from that video clip.
 
9. We can also upload multiple video files with a single **put file** command, and all will get processed:
 
   ```
   cd videos
   ls -1 | pachctl put file -i - videos@master
   ```
 
   The **-i -** flag tells the **put file** command to read input from stdin, which we're piping in from the **ls** command. The **-1** flag tells **ls** to display the files in a single column (i.e., one file per line), which is required for **put file** to process the list correctly. 
 
   Note that if you are running a small local cluster (via Minikube, for example), it may take upwards of 10 minutes for the pipeline job to complete the processing of the 5 included video files.

## Running The Python Code Locally
If you do want to run **extract\_video_frames.py** locally for whatever reason, you just need to specify the **-l** flag:
 
```
>> python ./extract_video_frames.py -l
```
 
In local mode, all of the files from the **./videos** directory will be processed, and the output will be written to the **./extracted_frames** directory.  If that directory doesn't exist, it will be created.
 