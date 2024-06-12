from pypylon import pylon
import cv2
import os
import time
import csv


class BaslerCamera:
    """
    A class to interact with a Basler camera using pypylon and OpenCV.
    """

    def __init__(self):
        """
        Initializes the BaslerCamera object and opens a connection to the first available camera.
        """
        self.basler_camera = pylon.InstantCamera(
            pylon.TlFactory.GetInstance().CreateFirstDevice()
        )
        self.basler_camera.Open()


    def set_frames_per_second(self, frames_per_second):
        """
        Sets the frame rate for the camera.

        Args:
            frames_per_second (float): The desired frame rate in frames per second.
        """
        self.frames_per_second = frames_per_second
        self.basler_camera.AcquisitionFrameRateEnable.SetValue(True)
        self.basler_camera.AcquisitionFrameRate.SetValue(self.frames_per_second)


    def set_output_file(self, path, extra_name, base_file_name='basler-camera'):
        """
        Sets the output file for recording the video.

        Args:
            path (str): The directory where the output file will be saved.
            extra_name (str): An additional name to be added to the base file name.
            base_file_name (str, optional): The base name of the output file. Defaults to 'basler-camera'.
        """
        fourcc = cv2.VideoWriter_fourcc(*'MP4V')

        frame_width = int(self.basler_camera.Width.Value)
        frame_height = int(self.basler_camera.Height.Value)

        # Construct the full output file name and path
        self.output_file_name = f"{base_file_name}_{extra_name}.mp4"
        self.output_path = os.path.join(path, self.output_file_name)

        # Create the VideoWriter object for recording
        self.out = cv2.VideoWriter(
            self.output_path, fourcc, self.frames_per_second, (frame_width, frame_height)
        )

        self.timestamps_file = os.path.join(path, f"{base_file_name}_{extra_name}_timestamps.csv")

        # Create the CSV file and write the header if it doesn't exist
        if not os.path.isfile(self.timestamps_file):
            with open(self.timestamps_file, mode='w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["timestamp"])


    def save_timestamp(self, timestamp):
        """
        Save the timestamp to a CSV file.
        
        Args:
            timestamp: The timestamp to be saved.
        """
        try:
            with open(self.timestamps_file, mode='a', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([timestamp])
        except Exception as e:
            print(f"Error saving timestamp: {e}")


    def set_timer(self, start_time):
        """
        Sets the timer for the camera.

        Args:
            start_time (float): The time at which the camera recording started.
        """
        self.start_time = start_time


    def start_recording(self):
        """
        Starts the camera recording.
        """
        self.frame_number = 1
        self.basler_camera.StartGrabbing()


    def stop_recording(self):
        """
        Stops the camera recording.
        """
        self.basler_camera.StopGrabbing()
        self.basler_camera.Close()

        if self.out is not None:
            self.out.release()


    def capture_frame(self):
        """
        Captures a single frame from the Basler camera, converts it to BGR color format,
        and writes it to the output file.
        """
        try:
            grab_result = self.basler_camera.RetrieveResult(
                5000, pylon.TimeoutHandling_ThrowException
            )
            if grab_result.GrabSucceeded():
                img = grab_result.Array
                img_bgr = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
                self.out.write(img_bgr)
                
                timestamp = time.time() - self.start_time
                self.save_timestamp(timestamp)

                self.frame_number += 1
            grab_result.Release()
        except Exception as e:
            print(f"Error during Basler capture: {e}")


    def save_metadata(self):
        """
        Saves metadata about the recording to a CSV file in the output directory.
        """
        metadata_file_name = f"{self.output_file_name.split('.')[0]}.csv"
        metadata_path = os.path.join(os.path.dirname(self.output_path), metadata_file_name)

        data = {
            "camera": "basler",
            "width": self.basler_camera.Width.Value,
            "height": self.basler_camera.Height.Value,
            "frame_rate_fps": self.frames_per_second,
            "output_file": self.output_file_name,
            "number_of_frames": self.frame_number
        }

        with open(metadata_path, mode='w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(data.keys())
            writer.writerow(data.values())