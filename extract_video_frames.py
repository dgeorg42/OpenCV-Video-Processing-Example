# 
# extract_video_frames.py
# 
# Author:	Dale Georg
# 
# This is a simple example of using the OpenCV library to extract frames
# from one or more video files. While it can be run on a local machine,
# the primary intention is to run it in a Docker container as part of a
# simple Pachyderm pipeline tutorial.
#
# Usage: python extract_video_frames.py [-l] [-h]
#	  The optional -l flag can be used to run locally.
#	  The optional -h flag will display the usage.
#
# Input: This module reads all video files in a directory.  That directory
# will be "/pfs/videos" by default to support reading from the Pachyderm
# file system.  Using the -l flag to run locally will change this
# directory to be "./videos" Note that OpenCV supports all video formats 
# that are supported by ffmpeg. Run "ffmpeg -formats" for the full list.
# 
# Output: The extracted video frames will be written out to a series of
# JPEG image files, named with the original filename as well as the frame
# number. Each video's images will be written to a different subdirectory
# of a base output directory. This base defaults to "/pfs/out", but will
# be "./extracted_videos" if run with the -l flag.
# 
# History:  2020/09/07 - Initial version published to Github.
#

import cv2
import os
import shutil
import sys
import getopt

# 
# Set variables to indicate the directory where the videos will be read from,
# as well as the directory to use as the root for storing the extracted frames.
# Also a variable to indicate if we are running locally.
#
video_directory = "/pfs/videos"
frame_directory_root = "/pfs/out"
run_locally = False

# 
# This function processes a single video file, specified by the input_dir
# and file_name parameters.
#
def process_video(input_dir, file_name):

	print("\r\n********** Processing " + file_name + "\r\n")

	# 
	# The output directory will be a directory in the frame_directory_root, given 
	# the same name of the video file we are processing.
	#
	output_dir = frame_directory_root + "/" + file_name

	# 
	# If we are running locally, we need to clean up and create the output directories.
	# Otherwise, we only need to ensure that the output sub-directory gets created on 
	# PFS. 
	#
	if True == run_locally:
		if not os.path.isdir(frame_directory_root):
			print("\tCreating frame directory root.")
			os.mkdir(frame_directory_root)

		if os.path.isdir(output_dir):
			print("\tLooks like this isn't your first rodeo; removing previous output directory for this video.")
			shutil.rmtree(output_dir) 
	
	if not os.path.isdir(output_dir):
		print("\tCreating output directory '" + output_dir + "'")
		os.mkdir(output_dir)

	# 
	# Read the video file using OpenCV's VideoCapture class.
	# 
	print("\tReading video file.")
	vid = cv2.VideoCapture(os.path.join(input_dir, file_name))

	frame_number = 0 # Counter for the frames we read

	while 1: # Loop until we get to the end of the video and break out

		# 
		# Print our progress every 100 frames.
		#
		if 0 == frame_number:
			print("\tStarting frame processing....")
		elif 0 == frame_number % 100:
			print("\t	 Processed " + str(frame_number) + " frames.")

		# 
		# Read the next frame. If rc is 0, this means there were no more frames, so we break out of the while loop.
		# If rc is NOT 0, we increment the frame_number counter, and write the image out with a filename that
		# incorporates the frame number (padded with zeros at the start).
		#
		rc, frame = vid.read() 
		if rc != 0:
			frame_number = frame_number + 1
			cv2.imwrite(output_dir + "/" + file_name + "--frame-" + str(frame_number).zfill(6) + ".jpg", frame)
		else:
			break;

	print("\r\n********** Done processing " + file_name + " - Total frames processed = " + str(frame_number))

#
# This function prints the help text.
#
def print_help():
	#print("\r\nUsage: python extract_video_frames.py [-l] [-h]")

	print("\nThis is a simple example of using the OpenCV library to extract frames")
	print("from one or more video files. While it can be run on a local machine,")
	print("the primary intention is to run it in a Docker container as part of a")
	print("simple Pachyderm pipeline tutorial.")
	print("\n\tUsage: python extract_video_frames.py [-l] [-h]")
	print("\t\tThe optional -l flag can be used to run locally.")
	print("\t\tThe optional -h flag will display the usage.")
	print("\nInput: This module reads all video files in a directory.  That directory")
	print("will be '/pfs/videos' by default to support reading from the Pachyderm")
	print("file system.  Using the -l flag to run locally will change this")
	print("directory to be './videos' Note that OpenCV supports all video formats")
	print("that are supported by ffmpeg. Run 'ffmpeg -formats' for the full list.")
	print("\nOutput: The extracted video frames will be written out to a series of")
	print("JPEG image files, named with the original filename as well as the frame")
	print("number. Each video's images will be written to a different subdirectory")
	print("of a base output directory. This base defaults to '/pfs/out but will',")
	print("be './extracted_videos' if run with the -l flag.")
	  
#
# The main function. Clearly. :)
#
def main(argv):

	print("\nSample Video Frame Extractor")
	print("****************************\n")

	# 
	# Get the arguments from the command line.  If an exception is thrown,
	# print the error message and the help text.
	try:
		opts, args = getopt.getopt(argv,"hl")
	except getopt.GetoptError as e:
		print(e.msg)
		print_help()
		sys.exit(2)

	# 
	# Process the command line arguments.  For -h, print the help and exit.
	# For -l, set the run_locally flag, update the directory names to use,
	# and continue.
	# 
	for opt, arg in opts:
		if opt == "-h":
			print_help()
			sys.exit()
		elif opt == "-l":
			global run_locally
			run_locally = True
			global video_directory
			video_directory = "./videos"
			global frame_directory_root
			frame_directory_root = "./extracted_frames"

	print("Videos will be read from: '" + video_directory + "'")
	print("Frame images will be written to sub-directories of '" + frame_directory_root + "'")
	print("Running in local mode?  " + str(run_locally).upper() + "\n")

	#
	# Walk the files in the video directory.  For each video, call the process_video function.
	#
	video_count = 0
	for dirpath, dirs, files in os.walk(video_directory):
		for file in files:
			process_video(dirpath, file)
			video_count = video_count + 1
	print("\nAll done! Videos processed: " + str(video_count) + "\nHave a nice day!\n")

#
# Kick it all off!
#
if __name__ == "__main__":
	main(sys.argv[1:])