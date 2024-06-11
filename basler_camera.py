from pypylon import pylon
import cv2
import os


class BaslerCamera:
    """
    A class to interact with a Basler camera using pypylon and OpenCV.
    """

    def __init__(self):
        """
        Initializes the BaslerCamera object and opens a connection to the first available camera.
        """
        self.camera_basler = pylon.InstantCamera(
            pylon.TlFactory.GetInstance().CreateFirstDevice()
        )
        self.camera_basler.Open()

    def set_frame_rate(self, frame_rate):
        """
        Sets the frame rate for the camera.

        Args:
            frame_rate (float): The desired frame rate in frames per second.
        """
        self.frame_rate = frame_rate
        self.camera_basler.AcquisitionFrameRateEnable.SetValue(True)
        self.camera_basler.AcquisitionFrameRateAbs.SetValue(frame_rate)

    def set_output_file(self, path, extra_name, base_file_name='basler-camera'):
        """
        Sets the output file for recording the video.

        Args:
            path (str): The directory where the output file will be saved.
            extra_name (str): An additional name to be added to the base file name.
            base_file_name (str, optional): The base name of the output file. Defaults to 'basler-camera'.
        """
        fourcc = cv2.VideoWriter_fourcc(*'MP4V')

        frame_width = int(self.camera_basler.Width.Value)
        frame_height = int(self.camera_basler.Height.Value)

        # Construct the full output file name and path
        self.output_file_name = f"{base_file_name}_{extra_name}.mp4"
        self.output_path = os.path.join(path, self.output_file_name)

        # Create the VideoWriter object for recording
        self.out = cv2.VideoWriter(
            self.output_path, fourcc, self.frame_rate, (frame_width, frame_height)
        )

    def start_recording(self):
        """
        Starts the camera recording.
        """
        self.camera_basler.StartGrabbing()

    def stop_recording(self):
        """
        Stops the camera recording.
        """
        self.camera_basler.StopGrabbing()
        self.Close()

        if self.out is not None:
            self.out.release()
